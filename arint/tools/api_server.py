# tools/api_server.py
import threading
import time
import logging
import hashlib
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from tools.seafil import Seafil
from tools.cleaners import abstract_knowledge

app = Flask(__name__)
arint_instance = None
lock = None

# Inisialisasi Limiter DI SINI, segera setelah app
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    headers_enabled=True,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded", "message": str(e.description)}), 429


@app.errorhandler(500)
def internal_error_handler(e):
    logger.error(f"Internal server error: {e}")
    return jsonify({"error": "Internal server error"}), 500


def run_api_server(arint, port, thread_lock):
    global arint_instance, lock
    arint_instance = arint
    lock = thread_lock
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


# ==================== HELPER ====================
def safe_lock_execute(func, *args, **kwargs):
    with lock:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error dalam safe_lock_execute: {e}")
            raise


# ==================== ENDPOINTS ====================
@app.route('/status', methods=['GET'])
@limiter.limit("30 per minute")
def status():
    logger.info(f"Status request from {request.remote_addr}")
    try:
        with lock:
            return jsonify({
                'cycle': arint_instance.cycle,
                'needs': arint_instance.needs,
                'insights_count': len(arint_instance.brain.insights),
                'snippets_count': len(arint_instance.brain.snippets)
            })
    except Exception as e:
        logger.exception("Gagal mengambil status")
        return jsonify({'error': 'Internal error'}), 500


@app.route('/learn', methods=['POST'])
@limiter.limit("10 per minute")
def learn():
    logger.info(f"Learn request from {request.remote_addr}")

    data = request.get_json()
    if not data or 'text' not in data:
        logger.warning("Learn request tanpa field 'text'")
        return jsonify({'error': 'Missing text'}), 400

    text = data['text'].strip()
    if not text:
        return jsonify({'error': 'Empty text'}), 400
    if len(text) > 1000:
        return jsonify({'error': 'Text too long (max 1000 chars)'}), 400

    source = data.get('source', 'external-api')

    try:
        with lock:
            filtered = arint_instance.seafil.process(text, source=source)
            if not filtered:
                logger.info("Tidak ada konten bermakna dari teks")
                return jsonify({'status': 'warning', 'message': 'No meaningful content extracted'}), 200

            abstracts = abstract_knowledge(filtered.content)
            if not abstracts:
                logger.info("Tidak ada abstraksi yang dihasilkan")
                return jsonify({'status': 'warning', 'message': 'No abstractions generated'}), 200

            for abs_ in abstracts:
                arint_instance.brain.add_snippet(abs_, source=source)
                key = f"ext_{hashlib.md5(abs_.encode()).hexdigest()[:8]}"
                arint_instance.memory.semantic.add_fact(
                    key, abs_, source=source, confidence=0.7
                )

            logger.info(f"Berhasil menambahkan {len(abstracts)} pengetahuan dari source '{source}'")
            return jsonify({'status': 'success', 'message': 'Knowledge added.'})

    except Exception as e:
        logger.exception("Error saat memproses /learn")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/ask', methods=['POST'])
@limiter.limit("20 per minute")
def ask():
    logger.info(f"Ask request from {request.remote_addr}")

    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing query'}), 400

    query = data['query'].strip()
    if not query:
        return jsonify({'error': 'Empty query'}), 400
    if len(query) > 200:
        return jsonify({'error': 'Query too long (max 200 chars)'}), 400

    try:
        with lock:
            snippets = arint_instance.brain.snippets[-5:]
            context = ' '.join(snippets)

        answer = arint_instance.transformer.generate(query + ' ' + context, max_new_tokens=50)

        logger.info(f"Query: {query[:50]}... -> Answer: {answer[:50]}...")
        return jsonify({'answer': answer})

    except Exception as e:
        logger.exception("Gagal menghasilkan jawaban")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/health', methods=['GET'])
@limiter.limit("1 per second")
def health():
    return jsonify({'status': 'alive'})


@app.route('/search', methods=['POST'])
@limiter.limit("15 per minute")
def search_memory():
    logger.info(f"Search request from {request.remote_addr}")

    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing query'}), 400

    query = data['query'].strip()
    if not query:
        return jsonify({'error': 'Empty query'}), 400
    if len(query) > 100:
        return jsonify({'error': 'Query too long (max 100 chars)'}), 400

    limit = data.get('limit', 10)
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        return jsonify({'error': 'Invalid limit (must be int 1-100)'}), 400

    try:
        with lock:
            results = []
            if hasattr(arint_instance.memory.semantic, 'search'):
                raw_results = arint_instance.memory.semantic.search(query, limit=limit)
                for res in raw_results:
                    results.append({
                        'key': res.get('key', 'unknown'),
                        'content': res.get('content', res.get('text', '')),
                        'confidence': res.get('confidence', 0.5)
                    })
            else:
                facts = getattr(arint_instance.memory.semantic, 'facts', {})
                query_lower = query.lower()
                for key, fact in facts.items():
                    if isinstance(fact, dict):
                        content = fact.get('content', fact.get('text', ''))
                        confidence = fact.get('confidence', 0.5)
                    else:
                        content = str(fact)
                        confidence = 0.5

                    if query_lower in content.lower():
                        results.append({
                            'key': key,
                            'content': content[:200] + '...' if len(content) > 200 else content,
                            'confidence': confidence
                        })
                        if len(results) >= limit:
                            break

            if not results and hasattr(arint_instance.brain, 'snippets'):
                snippets = arint_instance.brain.snippets[-50:]
                query_lower = query.lower()
                for snippet in snippets:
                    if query_lower in snippet.lower():
                        results.append({
                            'key': 'snippet',
                            'content': snippet[:200] + '...' if len(snippet) > 200 else snippet,
                            'confidence': 0.6
                        })
                        if len(results) >= limit:
                            break

            logger.info(f"Pencarian '{query}' menghasilkan {len(results)} hasil")
            return jsonify({'results': results})

    except Exception as e:
        logger.exception("Gagal melakukan pencarian")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/binary/analyze', methods=['POST'])
@limiter.limit("5 per minute")
def analyze_binary():
    logger.info(f"Binary analysis request from {request.remote_addr}")

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if request.content_length > 5 * 1024 * 1024:
        return jsonify({'error': 'File too large (max 5MB)'}), 400

    data = file.read()
    filename = file.filename

    try:
        from tools.binary_stream import AuxiliaryPerceptionChannel

        channel = AuxiliaryPerceptionChannel(
            chunk_size_bits=128,
            hidden_dims=[10, 6, 3],
            n_symbols=6
        )

        result = channel.process(data, train_epochs=100)

        with lock:
            summary = (
                f"Binary analysis of '{filename}': "
                f"{len(result['chunks'])} chunks, "
                f"{len(result['symbols'])} symbols, "
                f"anomalies: {len(result['anomalies'])}"
            )
            arint_instance.brain.add_snippet(summary, source=f"binary:{filename}")

            fact_key = f"binary_{filename}_{int(time.time())}"
            arint_instance.memory.semantic.add_fact(
                fact_key,
                {
                    'filename': filename,
                    'structure': result['structure'],
                    'anomalies': result['anomalies'],
                    'symbols': [s['label'] for s in result['symbols']],
                    'compression_ratio': result['compression_ratio'],
                },
                source="binary_analysis",
                confidence=0.8
            )

            if result['anomalies']:
                anomaly_insight = f"Anomaly detected in {filename}: {len(result['anomalies'])} anomalous chunks"
                arint_instance.brain.insights.append(anomaly_insight)
                arint_instance.memory.reflective.add_reflection({
                    'type': 'binary_anomaly',
                    'insight': anomaly_insight,
                    'timestamp': time.time()
                })

        logger.info(f"Binary analysis of '{filename}' completed")
        return jsonify({
            'status': 'success',
            'filename': filename,
            'chunks': len(result['chunks']),
            'symbols': len(result['symbols']),
            'anomalies': len(result['anomalies']),
            'structure': result['structure'],
            'compression_ratio': result['compression_ratio'],
        })

    except Exception as e:
        logger.exception("Error analyzing binary")
        return jsonify({'error': str(e)}), 500