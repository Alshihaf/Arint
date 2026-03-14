'''
Modul untuk validasi kode secara aman.
'''
import subprocess
import os
from pathlib import Path

DEFAULT_TIMEOUT = 5

def run_sandboxed_test(code_string, test_cases, timeout=DEFAULT_TIMEOUT):
    '''
    Menjalankan kode dalam sandbox terisolasi dan memvalidasinya terhadap test case.

    Args:
        code_string (str): Kode Python yang akan diuji.
        test_cases (list): Daftar tuple, masing-masing berisi (inputs, expected_output).
        timeout (int): Waktu maksimum eksekusi dalam detik.

    Returns:
        dict: Hasil validasi berisi status, output, dan pesan error.
    '''
    temp_dir = Path("memory/sandbox")
    temp_dir.mkdir(exist_ok=True)
    temp_file = temp_dir / "temp_code.py"

    # Buat kode pengujian lengkap
    full_code = [
        code_string, 
        "\n",
        "import sys",
        "import json",
        "\n",
        "def run_tests(tests):",
        "    results = []",
        "    for i, (inputs, expected) in enumerate(tests):",
        "        try:",
        # Ekstrak nama fungsi utama dari AST
        "            func_name = [n.name for n in ast.parse(code_string).body if isinstance(n, ast.FunctionDef)][0]",
        f"           actual = {func_name}(*inputs)",
        "            results.append({",
        "                'test': i,",
        "                'status': 'pass' if actual == expected else 'fail',",
        "                'actual': actual,",
        "                'expected': expected",
        "            })",
        "        except Exception as e:",
        "            results.append({",
        "                'test': i,",
        "                'status': 'error',",
        "                'error': str(e)",
        "            })",
        "    print(json.dumps(results))",
        "\n",
        "if __name__ == '__main__':",
        "    test_data = json.loads(sys.argv[1])",
        "    run_tests(test_data)",
        "\n"
    ]
    
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write("\n".join(full_code))

    try:
        # Jalankan sebagai proses terpisah
        test_cases_json = json.dumps(test_cases)
        process = subprocess.run(
            [sys.executable, str(temp_file), test_cases_json],
            capture_output=True, text=True, timeout=timeout, check=False
        )

        if process.returncode != 0:
            return {
                "status": "execution_error",
                "stdout": process.stdout,
                "stderr": process.stderr,
                "reason": "Kode gagal dieksekusi atau error saat runtime."
            }
        
        # Parse hasil JSON dari stdout
        test_results = json.loads(process.stdout)
        total = len(test_results)
        passed = sum(1 for r in test_results if r['status'] == 'pass')

        if passed == total:
            return {"status": "success", "passed": passed, "total": total, "details": test_results}
        else:
            return {"status": "failure", "passed": passed, "total": total, "details": test_results}

    except subprocess.TimeoutExpired:
        return {"status": "timeout", "reason": f"Eksekusi melebihi {timeout} detik."}
    except Exception as e:
        return {"status": "validation_error", "reason": f"Error pada sistem validasi: {e}"}
    finally:
        # Selalu bersihkan file sementara
        if os.path.exists(temp_file):
            os.remove(temp_file)
