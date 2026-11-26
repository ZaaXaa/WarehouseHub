# ==============================================================================
# APLIKASI WAREHOUSEHUB - BACKEND (FLASK)
# Mata Kuliah: Komputasi Awan dan Terdistribusi
# ==============================================================================

# Mengimpor modul-modul yang dibutuhkan dari Flask
from flask import Flask, jsonify, request, render_template
# Mengimpor datetime untuk mencatat waktu transaksi secara otomatis
from datetime import datetime

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# ==============================================================================
# DATABASE SIMULASI (JSON/DICT) - 3 ENTITAS
# Sesuai syarat tugas: Tidak menggunakan database SQL, hanya JSON/DICT
# ==============================================================================
db = {
    # Entitas 1: Barang (Master data stok gudang)
    "barang": {
        1: {"id": 1, "sku": "PKG-001", "nama": "Corrugated box - Medium", "dimensi": "32 x 24 x 20 cm", "kategori": "Packaging", "lokasi": "A-01-02", "stok": 1240, "harga": 5000, "supplier_id": 1, "updated": "Today, 09:42"},
        2: {"id": 2, "sku": "PKG-002", "nama": "Stretch wrap - Clear", "dimensi": "500 mm x 300 m", "kategori": "Packaging", "lokasi": "A-02-01", "stok": 32, "harga": 15000, "supplier_id": 1, "updated": "Today, 09:35"},
        3: {"id": 3, "sku": "SAF-014", "nama": "Nitrile gloves - Large", "dimensi": "Box of 100 - Blue", "kategori": "Safety & PPE", "lokasi": "B-03-04", "stok": 480, "harga": 25000, "supplier_id": 2, "updated": "Today, 09:18"},
        4: {"id": 4, "sku": "PKG-008", "nama": "Packing tape - Brown", "dimensi": "48 mm x 100 m", "kategori": "Packaging", "lokasi": "A-01-05", "stok": 0, "harga": 8000, "supplier_id": 1, "updated": "Today, 08:56"},
        5: {"id": 5, "sku": "LBL-003", "nama": "Thermal shipping labels", "dimensi": "100 x 150 mm - Roll of 500", "kategori": "Labels", "lokasi": "C-01-02", "stok": 864, "harga": 12000, "supplier_id": 3, "updated": "Today, 08:41"},
        6: {"id": 6, "sku": "SAF-021", "nama": "Safety vest - Hi-vis", "dimensi": "Size XL - Reflective", "kategori": "Safety & PPE", "lokasi": "B-02-03", "stok": 16, "harga": 35000, "supplier_id": 2, "updated": "Yesterday"},
    },
    # Entitas 2: Supplier (Data pemasok barang)
    "supplier": {
        1: {"id": 1, "nama": "PT Packaging Indonesia", "kontak": "081234567890", "alamat": "Jakarta"},
        2: {"id": 2, "nama": "PT Safety First Global", "kontak": "081987654321", "alamat": "Surabaya"},
        3: {"id": 3, "nama": "PT Label Master", "kontak": "081122334455", "alamat": "Bandung"},
    },
    # Entitas 3: Transaksi (Riwayat keluar masuk barang)
    "transaksi": {
        1: {"id": 1, "jenis": "Masuk", "jumlah": 340, "tanggal": "Today, 09:15", "barang_id": 4, "deskripsi": "Restock packing tape"},
        2: {"id": 2, "jenis": "Keluar", "jumlah": 50, "tanggal": "Today, 09:30", "barang_id": 3, "deskripsi": "Order shipped"},
    },
}

# ==============================================================================
# ROUTING HALAMAN UTAMA (FRONTEND)
# ==============================================================================
@app.route('/')
def index():
    """Merender file index.html yang ada di folder templates"""
    return render_template('index.html')

# ==============================================================================
# API: DASHBOARD (Menghitung Statistik untuk Cards)
# ==============================================================================
@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """Menghitung dan mengembalikan data statistik untuk dashboard"""
    total_stok = sum(b["stok"] for b in db["barang"].values())
    total_produk = len(db["barang"])
    low_stock = sum(1 for b in db["barang"].values() if 0 < b["stok"] <= 50)
    out_of_stock = sum(1 for b in db["barang"].values() if b["stok"] == 0)
    total_supplier = len(db["supplier"])
    total_masuk = sum(t["jumlah"] for t in db["transaksi"].values() if t["jenis"] == "Masuk")
    total_keluar = sum(t["jumlah"] for t in db["transaksi"].values() if t["jenis"] == "Keluar")
    
    return jsonify({
        "total_stok": total_stok, "total_produk": total_produk,
        "low_stock": low_stock, "out_of_stock": out_of_stock,
        "total_supplier": total_supplier,
        "total_masuk": total_masuk, "total_keluar": total_keluar
    })

# ==============================================================================
# API: READ BARANG (Dengan Fitur Low Stock Alert)
# ==============================================================================
@app.route('/api/barang', methods=['GET'])
def get_barang():
    """Mengambil semua data barang dan menambahkan status warna"""
    list_barang = list(db["barang"].values())
    for b in list_barang:
        # Menggabungkan nama supplier (Multi-entity feature)
        b["nama_supplier"] = db["supplier"].get(b.get("supplier_id"), {}).get("nama", "Unknown")
        
        # Logika Low Stock Alert
        if b["stok"] == 0:
            b["status"] = "Out of stock"; b["warna"] = "red"
        elif b["stok"] <= 50:
            b["status"] = "Low stock"; b["warna"] = "orange"
        else:
            b["status"] = "In stock"; b["warna"] = "green"
    return jsonify(list_barang)

# ==============================================================================
# API: CREATE BARANG (AUTO GENERATE TRANSAKSI MASUK)
# ==============================================================================
@app.route('/api/barang', methods=['POST'])
def add_barang():
    """Menambah barang baru dan otomatis membuat catatan transaksi masuk"""
    data = request.json
    new_id = max(db["barang"].keys()) + 1 if db["barang"] else 1
    data["id"] = new_id
    data["updated"] = datetime.now().strftime("Today, %H:%M")
    db["barang"][new_id] = data

    # 🌟 LOGIKA PENTING: Otomatis buat Transaksi Masuk saat Add Stock
    trx_id = max(db["transaksi"].keys()) + 1 if db["transaksi"] else 1
    trx_data = {
        "id": trx_id,
        "jenis": "Masuk",
        "jumlah": data.get("stok", 0),
        "tanggal": data["updated"],
        "barang_id": new_id,
        "deskripsi": "Initial stock added (Add New Stock)"
    }
    db["transaksi"][trx_id] = trx_data

    return jsonify(data), 201

# ==============================================================================
# API: UPDATE BARANG
# ==============================================================================
@app.route('/api/barang/<int:item_id>', methods=['PUT'])
def update_barang(item_id):
    """Mengupdate data barang yang sudah ada"""
    if item_id not in db["barang"]:
        return jsonify({"error": "Not found"}), 404
    db["barang"][item_id].update(request.json)
    return jsonify(db["barang"][item_id])

# ==============================================================================
# API: DELETE BARANG
# ==============================================================================
@app.route('/api/barang/<int:item_id>', methods=['DELETE'])
def delete_barang(item_id):
    """Menghapus data barang"""
    if item_id not in db["barang"]:
        return jsonify({"error": "Not found"}), 404
    del db["barang"][item_id]
    return jsonify({"message": "Barang berhasil dihapus"})

# ==============================================================================
# API: CRUD SUPPLIER
# ==============================================================================
@app.route('/api/supplier', methods=['GET'])
def get_supplier():
    """Mengambil semua data supplier"""
    return jsonify(list(db["supplier"].values()))

@app.route('/api/supplier', methods=['POST'])
def add_supplier():
    """Menambah supplier baru"""
    data = request.json
    new_id = max(db["supplier"].keys()) + 1 if db["supplier"] else 1
    data["id"] = new_id
    db["supplier"][new_id] = data
    return jsonify(data), 201

@app.route('/api/supplier/<int:sup_id>', methods=['DELETE'])
def delete_supplier(sup_id):
    """Menghapus supplier"""
    if sup_id not in db["supplier"]:
        return jsonify({"error": "Not found"}), 404
    del db["supplier"][sup_id]
    return jsonify({"message": "Supplier berhasil dihapus"})

# ==============================================================================
# API: READ TRANSAKSI (Multi-Entity Join)
# ==============================================================================
@app.route('/api/transaksi', methods=['GET'])
def get_transaksi():
    """Mengambil transaksi dan menggabungkannya dengan data barang"""
    list_trx = []
    for t in db["transaksi"].values():
        t_copy = t.copy()
        barang = db["barang"].get(t["barang_id"], {})
        t_copy["nama_barang"] = barang.get("nama", "Unknown")
        t_copy["dimensi"] = barang.get("dimensi", "")
        t_copy["kategori"] = barang.get("kategori", "")
        list_trx.append(t_copy)
    return jsonify(list_trx)

# ==============================================================================
# API: CREATE TRANSAKSI (Auto Update Stok)
# ==============================================================================
@app.route('/api/transaksi', methods=['POST'])
def add_transaksi():
    """Menambah transaksi dan mengupdate stok barang secara otomatis"""
    data = request.json
    new_id = max(db["transaksi"].keys()) + 1 if db["transaksi"] else 1
    data["id"] = new_id
    data["tanggal"] = datetime.now().strftime("Today, %H:%M")
    db["transaksi"][new_id] = data
    
    # Update stok barang
    barang_id = data.get("barang_id")
    if barang_id in db["barang"]:
        if data["jenis"] == "Masuk":
            db["barang"][barang_id]["stok"] += data["jumlah"]
        elif data["jenis"] == "Keluar":
            db["barang"][barang_id]["stok"] -= data["jumlah"]
        db["barang"][barang_id]["updated"] = data["tanggal"]
    return jsonify(data), 201

# ==============================================================================
# API: DELETE TRANSAKSI (Reverse Stok)
# ==============================================================================
@app.route('/api/transaksi/<int:trx_id>', methods=['DELETE'])
def delete_transaksi(trx_id):
    """Menghapus transaksi dan mengembalikan stok seperti semula"""
    if trx_id not in db["transaksi"]:
        return jsonify({"error": "Not found"}), 404
    trx = db["transaksi"][trx_id]
    barang_id = trx.get("barang_id")
    if barang_id in db["barang"]:
        if trx["jenis"] == "Masuk":
            db["barang"][barang_id]["stok"] -= trx["jumlah"]
        elif trx["jenis"] == "Keluar":
            db["barang"][barang_id]["stok"] += trx["jumlah"]
    del db["transaksi"][trx_id]
    return jsonify({"message": "Transaksi berhasil dihapus"})

# ==============================================================================
# FITUR MULTI-ENTITAS: Laporan per Supplier
# (Memenuhi syarat: minimal 1 fitur pakai 2+ entitas)
# ==============================================================================
@app.route('/api/laporan/supplier/<int:supplier_id>', methods=['GET'])
def laporan_supplier(supplier_id):
    """Mengambil riwayat transaksi khusus untuk satu supplier tertentu"""
    if supplier_id not in db["supplier"]:
        return jsonify({"error": "Supplier tidak ditemukan"}), 404
    
    supplier = db["supplier"][supplier_id]
    riwayat = []
    
    # Menggabungkan data Transaksi, Barang, dan Supplier
    for t in db["transaksi"].values():
        barang = db["barang"].get(t["barang_id"], {})
        if barang.get("supplier_id") == supplier_id:
            t_copy = t.copy()
            t_copy["nama_barang"] = barang.get("nama", "Unknown")
            riwayat.append(t_copy)
            
    return jsonify({"supplier": supplier["nama"], "riwayat_transaksi": riwayat})

# ==============================================================================
# MENJALANKAN SERVER FLASK
# ==============================================================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)