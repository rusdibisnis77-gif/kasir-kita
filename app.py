import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 1. KONFIGURASI HALAMAN & STYLE CSS (TAMPILAN BERSIH)
# ==========================================
st.set_page_config(page_title="Aplikasi Kasir Digital", layout="wide")

# Trik CSS untuk menyembunyikan tombol + dan - serta merapikan input angka
st.markdown(
    """
    <style>
    /* Menghilangkan tombol plus minus (+ / -) bawaan Streamlit */
    button[title="Incriment/Decrement values"], 
    button[data-testid="stNumberInputStepUp"], 
    button[data-testid="stNumberInputStepDown"] {
        display: none !important;
    }
    /* Memastikan tampilan kolom tetap rapi setelah tombol hilang */
    div[data-testid="stNumberInputContainer"] {
        padding-right: 10px !important;
    }
    /* Desain Struk Thermal */
    .struk-container {
        font-family: 'Courier New', Courier, monospace;
        background-color: #ffffff;
        color: #000000;
        padding: 20px;
        border: 1px solid #ccc;
        max-width: 400px;
        margin: 0 auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. INISIALISASI DATABASE SIMPEL (SESSION STATE)
# ==========================================
if 'produk' not in st.session_state:
    st.session_state.produk = pd.DataFrame([
        {"Barcode/ID": "8991001", "Nama Barang": "Minyak Goreng 1L", "Harga Satuan": 18000, "Stok": 20},
        {"Barcode/ID": "8991002", "Nama Barang": "Gula Pasir 1kg", "Harga Satuan": 15000, "Stok": 15},
        {"Barcode/ID": "8991003", "Nama Barang": "Beras Premium 5kg", "Harga Satuan": 75000, "Stok": 10}
    ])

if 'keranjang' not in st.session_state:
    st.session_state.keranjang = []

if 'utang' not in st.session_state:
    st.session_state.utang = pd.DataFrame([
        {"Nama Pelanggan": "Budi", "Sisa Utang": 50000, "Tanggal Utang": "2026-07-10"}
    ])

# ==========================================
# 3. NAVIGASI MENU UTAMA
# ==========================================
menu = st.sidebar.radio("PILIH MENU", ["Kasir", "Pelunasan Utang", "Kelola Barang", "Koreksi Stok"])

# ==========================================
# MENU 1: KASIR
# ==========================================
if menu == "Kasir":
    st.title("🛒 Menu Kasir (Transaksi)")
    
    # Fitur Simulasi Barcode / Pencarian Kilat Keyboard
    search_query = st.text_input("Simulasi Barcode / Cari Nama Produk (Ketik lalu tekan Enter)", key="search_barcode")
    
    selected_product = None
    if search_query:
        # Cari berdasarkan kecocokan ID/Barcode atau Nama Barang
        df_res = st.session_state.produk[
            st.session_state.produk['Barcode/ID'].str.contains(search_query, case=False) | 
            st.session_state.produk['Nama Barang'].str.contains(search_query, case=False)
        ]
        if not df_res.empty:
            selected_product = df_res.iloc[0]
            st.success(f"Terpilih otomatis: {selected_product['Nama Barang']} (Rp {selected_product['Harga Satuan']:,})")
        else:
            st.warning("Produk tidak ditemukan.")

    # Kolom Input Transaksi
    col1, col2 = st.columns(2)
    with col1:
        # Jika ada produk dari pencarian barcode otomatis diisi, jika tidak pilih manual
        daftar_nama_produk = st.session_state.produk['Nama Barang'].tolist()
        idx_default = daftar_nama_produk.index(selected_product['Nama Barang']) if selected_product is not None else 0
        
        produk_pilihan = st.selectbox("Pilih Produk Manual", daftar_nama_produk, index=idx_default)
        data_produk = st.session_state.produk[st.session_state.produk['Nama Barang'] == produk_pilihan].iloc[0]
        
        # Kolom input Jumlah Beli (Nol otomatis hilang & tanda +/- hilang)
        jumlah_beli = st.number_input("Jumlah beli", min_value=1, value=None, placeholder="Masukkan jumlah...")

    with col2:
        # Potongan Harga & Uang Tunai (Nol otomatis hilang & tanda +/- hilang)
        potongan_harga = st.number_input("Potongan harga (Rp)", min_value=0, value=None, placeholder="0")
        uang_tunai = st.number_input("Uang tunai / Nominal Bayar (Rp)", min_value=0, value=None, placeholder="0")

    # Tombol Tambah ke Keranjang
    if st.button("Tambah ke Keranjang"):
        if jumlah_beli is not None:
            if jumlah_beli <= data_produk['Stok']:
                potongan = potongan_harga if potongan_harga is not None else 0
                subtotal = (data_produk['Harga Satuan'] * jumlah_beli) - potongan
                
                st.session_state.keranjang.append({
                    "Nama Barang": data_produk['Nama Barang'],
                    "Harga Satuan": data_produk['Harga Satuan'],
                    "Jumlah": jumlah_beli,
                    "Potongan": potongan,
                    "Subtotal": subtotal
                })
                st.success(f"{data_produk['Nama Barang']} berhasil dimasukkan!")
                st.rerun()
            else:
                st.error("Stok barang di gudang tidak mencukupi!")
        else:
            st.warning("Masukkan jumlah beli terlebih dahulu.")

    # Tabel Keranjang Belanjaan
    if st.session_state.keranjang:
        st.subheader("🛒 Daftar Belanja")
        df_keranjang = pd.DataFrame(st.session_state.keranjang)
        st.dataframe(df_keranjang, use_container_width=True)
        
        total_belanja = df_keranjang['Subtotal'].sum()
        st.markdown(f"### **TOTAL HARGA: Rp {total_belanja:,}**")
        
        if st.button("Kosongkan Keranjang"):
            st.session_state.keranjang = []
            st.rerun()
            
        # Proses Pembayaran & Cetak Struk Format WhatsApp / Thermal Rata Kiri-Kanan
        if uang_tunai is not None:
            kembalian = uang_tunai - total_belanja
            if kembalian >= 0:
                st.success(f"Pembayaran Valid. Kembalian: Rp {kembalian:,}")
                
                # Pembuatan teks struk rapi rata kiri-kanan
                garis = "--------------------------------"
                waktu_skrg = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                struk_teks = f"        TOKO MANUNGGAL        \n"
                struk_teks += f"      {waktu_skrg}      \n"
                struk_teks += f"{garis}\n"
                
                for item in st.session_state.keranjang:
                    nama = item['Nama Barang'][:15]
                    qty_harga = f"{item['Jumlah']}x{item['Harga Satuan']:,}"
                    sub = f"Rp{item['Subtotal']:,}"
                    spasi1 = " " * (32 - len(nama) - len(sub))
                    struk_teks += f"{nama}{spasi1}{sub}\n"
                    struk_teks += f"  Diskon: Rp{item['Potongan']:,}\n"
                    
                struk_teks += f"{garis}\n"
                tot_str = f"Rp{total_belanja:,}"
                spasi_tot = " " * (32 - 13 - len(tot_str))
                struk_teks += f"TOTAL BELANJA{spasi_tot}{tot_str}\n"
                
                tun_str = f"Rp{uang_tunai:,}"
                spasi_tun = " " * (32 - 10 - len(tun_str))
                struk_teks += f"TUNAI/BAYAR{spasi_tun}{tun_str}\n"
                
                kem_str = f"Rp{kembalian:,}"
                spasi_kem = " " * (32 - 9 - len(kem_str))
                struk_teks += f"KEMBALIAN{spasi_kem}{kem_str}\n"
                struk_teks += f"{garis}\n"
                struk_teks += f"   Terima Kasih Atas Kunjungan   \n"
                struk_teks += f"            Anda!               "
                
                st.subheader("📄 Salin Nota / Cetak Struk")
                st.text_area("Salin teks di bawah ini untuk dikirim ke WhatsApp atau dicetak ke Printer Thermal:", value=struk_teks, height=350)
            else:
                st.error(f"Uang tunai kurang sebesar: Rp {abs(kembalian):,}")

# ==========================================
# MENU 2: PELUNASAN UTANG
# ==========================================
elif menu == "Pelunasan Utang":
    st.title("🤝 Menu Pelunasan Utang Pelanggan")
    st.dataframe(st.session_state.utang, use_container_width=True)
    
    if not st.session_state.utang.empty:
        pelanggan_list = st.session_state.utang['Nama Pelanggan'].tolist()
        pilih_pelanggan = st.selectbox("Pilih nama pelanggan yang bayar utang", pelanggan_list)
        
        # Input Nominal Pembayaran (Nol otomatis hilang & tanda +/- hilang)
        nominal_pembayaran = st.number_input("Nominal pembayaran utang (Rp)", min_value=0, value=None, placeholder="0")
        
        if st.button("Proses Bayar Utang"):
            if nominal_pembayaran is not None and nominal_pembayaran > 0:
                idx = st.session_state.utang[st.session_state.utang['Nama Pelanggan'] == pilih_pelanggan].index[0]
                sisa = st.session_state.utang.at[idx, 'Sisa Utang'] - nominal_pembayaran
                
                if sisa <= 0:
                    st.success(f"Utang atas nama {pilih_pelanggan} LUNAS!")
                    st.session_state.utang = st.session_state.utang.drop(idx).reset_index(drop=True)
                else:
                    st.session_state.utang.at[idx, 'Sisa Utang'] = sisa
                    st.success(f"Pembayaran berhasil dimasukkan. Sisa utang {pilih_pelanggan} sekarang: Rp {sisa:,}")
                st.rerun()
            else:
                st.warning("Masukkan nominal pembayaran utang valid.")

# ==========================================
# MENU 3: KELOLA BARANG
# ==========================================
elif menu == "Kelola Barang":
    st.title("📦 Kelola Barang & Tambah Produk Baru")
    st.dataframe(st.session_state.produk, use_container_width=True)
    
    st.subheader("➕ Daftarkan Produk Baru / Tambah Stok")
    col1, col2 = st.columns(2)
    with col1:
        barcode_baru = st.text_input("Barcode / ID Produk Baru")
        nama_baru = st.text_input("Nama barang / produk")
    with col2:
        # Harga Jual Satuan & Jumlah Stok Masuk (Nol otomatis hilang & tanda +/- hilang)
        harga_jual_satuan = st.number_input("Harga jual satuan (Rp)", min_value=0, value=None, placeholder="0")
        jumlah_stok_masuk = st.number_input("Jumlah stok masuk", min_value=1, value=None, placeholder="0")
        
    if st.button("Simpan ke Gudang"):
        if barcode_baru and nama_baru and harga_jual_satuan is not None and jumlah_stok_masuk is not None:
            # Cek apakah kode barang sudah terdaftar
            if barcode_baru in st.session_state.produk['Barcode/ID'].values:
                # Update stok jika barcode sudah ada
                idx = st.session_state.produk[st.session_state.produk['Barcode/ID'] == barcode_baru].index[0]
                st.session_state.produk.at[idx, 'Stok'] += jumlah_stok_masuk
                st.success(f"Stok produk {nama_baru} berhasil ditambah!")
            else:
                # Tambah produk baru jika barcode belum ada
                baru = pd.DataFrame([{"Barcode/ID": barcode_baru, "Nama Barang": nama_baru, "Harga Satuan": harga_jual_satuan, "Stok": jumlah_stok_masuk}])
                st.session_state.produk = pd.concat([st.session_state.produk, baru], ignore_index=True)
                st.success(f"Produk baru '{nama_baru}' berhasil didaftarkan!")
            st.rerun()
        else:
            st.error("Gagal menyimpan, mohon lengkapi semua data input di atas.")

# ==========================================
# MENU 4: KOREKSI STOK
# ==========================================
elif menu == "Koreksi Stok":
    st.title("🔧 Koreksi Jumlah Stok & Penyesuaian Harga")
    st.dataframe(st.session_state.produk, use_container_width=True)
    
    daftar_produk_koreksi = st.session_state.produk['Nama Barang'].tolist()
    pilih_koreksi = st.selectbox("Pilih produk yang ingin disesuaikan datanya", daftar_produk_koreksi)
    
    data_koreksi = st.session_state.produk[st.session_state.produk['Nama Barang'] == pilih_koreksi].iloc[0]
    
    col1, col2 = st.columns(2)
    with col1:
        # Sesuaikan Harga Satuan Baru (Nol otomatis hilang & tanda +/- hilang)
        harga_satuan_baru = st.number_input("Sesuaikan harga satuan baru (Rp)", min_value=0, value=None, placeholder=str(data_koreksi['Harga Satuan']))
    with col2:
        # Koreksi Jumlah Stok Gudang (Nol otomatis hilang & tanda +/- hilang)
        koreksi_jumlah_stok = st.number_input("Koreksi jumlah stok baru di gudang", min_value=0, value=None, placeholder=str(data_koreksi['Stok']))
        
    if st.button("Terapkan Koreksi"):
        idx = st.session_state.produk[st.session_state.produk['Nama Barang'] == pilih_koreksi].index[0]
        
        # Eksekusi update jika kasir memasukkan nominal baru
        if harga_satuan_baru is not None:
            st.session_state.produk.at[idx, 'Harga Satuan'] = harga_satuan_baru
        if koreksi_jumlah_stok is not None:
            st.session_state.produk.at[idx, 'Stok'] = koreksi_jumlah_stok
            
        st.success(f"Data produk '{pilih_koreksi}' berhasil diperbarui di server!")
        st.rerun()
