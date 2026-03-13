#!/bin/bash
# Skrip Instalasi Library Dependencies untuk Arint
# Dioptimalkan untuk Termux Android

echo "=========================================="
echo "Menginstall Dependencies untuk Arint"
echo "=========================================="
echo ""

# Update pip terlebih dahulu
echo "[1/2] Mengupdate pip..."
pip install --upgrade pip --break-system-packages

echo ""
echo "[2/2] Menginstall library dependencies..."
echo ""

# Instalasi library satu per satu dengan feedback
pip install flask==2.3.3 --break-system-packages && echo "✓ Flask terinstall"
pip install requests==2.31.0 --break-system-packages && echo "✓ Requests terinstall"
pip install sqlalchemy==2.0.21 --break-system-packages && echo "✓ SQLAlchemy terinstall"
pip install numpy==1.24.3 --break-system-packages && echo "✓ NumPy terinstall"

# Optional: Development tools
echo ""
echo "Menginstall optional development tools..."
pip install pytest==7.4.2 --break-system-packages && echo "✓ Pytest terinstall"
pip install black==23.9.1 --break-system-packages && echo "✓ Black terinstall"
pip install flake8==6.1.0 --break-system-packages && echo "✓ Flake8 terinstall"

echo ""
echo "=========================================="
echo "Instalasi selesai!"
echo "=========================================="
echo ""
echo "Verifikasi instalasi dengan menjalankan:"
echo "python -c \"import flask, requests, sqlalchemy, numpy; print('All libraries installed successfully')\""