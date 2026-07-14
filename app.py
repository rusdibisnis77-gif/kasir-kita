import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Kasir Kita - Aplikasi Kasir Toko Online",
    page_icon="🛍️",
    layout="wide"
)

# --- KONEKSI SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    try:
        # Membersihkan spasi atau path '/rest/v1/' yang tidak sengaja terbaca
        url = st.secrets["SUPABASE_URL"].strip().replace("/rest/v1/", "").replace("/rest/v1", "")
        key = st.secrets["SUPABASE_KEY"].strip()
        return create_client(url, key)
    except Exception as e:
        st.error("Gagal terhubung ke database. Pastikan Secrets 'SUPABASE_URL' dan 'SUPABASE_KEY' sudah diisi di Streamlit Cloud!")
        st.stop()

supabase = init_supabase()

# --- STATE MANAGMENT ---
if "user_session" not in st.session_state:
    st.session_state.user_session = None  # Menyimpan data user yang login (id, nama_toko, username)
if "keranjang" not in st.session_state:
    st.session_state.keranjang = []  # Menyimpan barang belanjaan sementara

# --- FUNGSI DATABASE ---
def daftar_user(username, password, nama_toko):
    try:
        # Cek apakah username sudah terdaftar
        res = supabase.table("users").select("*").eq("username", username).execute()
        if len(res.data) > 0:
            return False, "Username sudah digunakan oleh toko lain!"
        
        # Simpan user baru
        data = {
            "username": username,
            "password": password,  # Pada sistem produksi sangat disarankan menggunakan hashing password
            "nama_toko": nama_toko
        }
        supabase.table("users").insert(data).execute()
        return True, "Akun Toko berhasil didaftarkan! Silakan masuk."
    except Exception as e:
        return False, f"Terjadi kesalahan: {str(e)}"

def login_user(username, password):
    try:
        res = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
        if len(res.data) == 1:
            return True, res.data[0]
        return False, "Username atau Password salah!"
    except Exception as e:
        return False, f"Terjadi kesalahan: {str(e)}"

def ambil_produk(user_id):
    try:
        res = supabase.table("produk").select("*").eq("user_id", user_id).order("nama_produk").execute()
        return res.data
    except:
        return []

def tambah_produk(user_id, nama, harga, stok, kode=""):
    try:
        data = {
            "user_id": user_id,
            "nama_produk": nama,
            "harga": int(harga),
            "stok": int(stok),
            "kode_produk": kode
        }
        supabase.table("produk").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Gagal menambah produk: {str(e)}")
        return False

def update_stok(produk_id, stok_baru):
    try:
        supabase.table("produk").update({"stok": int(stok_baru)}).eq("id", produk_id).execute()
    except Exception as e:
        st.error(f"Gagal memperbarui stok: {str(e)}")

def hapus_produk(produk_id):
    try:
        supabase.table("produk").delete().eq("id", produk_id).execute()
        return True
    except Exception as e:
        st.error(f"Gagal menghapus produk: {str(e)}")
        return False

def ambil_utang(user_id):
    try:
        res = supabase.table("utang").select("*").eq("user_id", user_id).order("id", desc=True).execute()
        return res.data
    except:
        return []

def tambah_utang(user_id, nama_pelanggan, sisa_utang):
    try:
        data = {
            "user_id": user_id,
            "nama_pelanggan": nama_pelanggan,
            "sisa_utang": int(sisa_utang)
        }
        supabase.table("utang").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Gagal mencatat utang: {str(e)}")
        return False

def bayar_utang_db(utang_id, nominal_bayar, sisa_sebelumnya):
    try:
        sisa_baru = max(0, sisa_sebelumnya - nominal_bayar)
        if sisa_baru == 0:
            supabase.table("utang").delete().eq("id", utang_id).execute()
        else:
            supabase.table("utang").update({"sisa_utang": sisa_baru}).eq("id", utang_id).execute()
        return True
    except Exception as e:
        st.error(f"Gagal memperbarui utang: {str(e)}")
        return False


# =========================================================================
# --- HALAMAN AUTENTIKASI (LOGIN & DAFTAR) ---
# =========================================================================
if st.session_state.user_session is None:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🛍️ Kasir Kita</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #555;'>Sistem Kasir Online Toko Anda Aman & Tersimpan di Cloud</p>", unsafe_allow_html=True)
    
    tab_login, tab_daftar = st.tabs(["🔐 Masuk Akun", "📝 Daftar Akun Baru"])
    
    with tab_login:
        st.subheader("Silakan Masuk ke Toko Anda")
        login_username = st.text_input("Username", key="l_username")
        login_password = st.text_input("Password", type="password", key="l_password")
        
        if st.button("Masuk Sekarang", use_container_width=True, type="primary"):
            if login_username and login_password:
                success, response = login_user(login_username, login_password)
                if success:
                    st.session_state.user_session = response
                    st.success(f"Selamat Datang Kembali di {response['nama_toko']}! 🎉")
                    st.rerun()
                else:
                    st.error(response)
            else:
                st.warning("Mohon isi semua kolom login!")

    with tab_daftar:
        st.subheader("Daftarkan Toko Baru Anda")
        reg_nama_toko = st.text_input("Nama Toko / Bisnis", placeholder="Contoh: Toko Berkah Mandiri")
        reg_username = st.text_input("Username Baru (Tanpa Spasi)", placeholder="Contoh: tokoberkah")
        reg_password = st.text_input("Password Baru", type="password")
        
        if st.button("Daftar Sekarang", use_container_width=True):
            if reg_nama_toko and reg_username and reg_password:
                if " " in reg_username:
                    st.error("Username tidak boleh mengandung spasi!")
                else:
                    success, message = daftar_user(reg_username, reg_password, reg_nama_toko)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
            else:
                st.warning("Mohon isi semua data pendaftaran!")


# =========================================================================
# --- HALAMAN UTAMA APLIKASI (JIKA SUDAH LOGIN) ---
# =========================================================================
else:
    user = st.session_state.user_session
    
    # --- Sidebar Navigasi & Info Toko ---
    with st.sidebar:
        st.markdown(f"### 🏪 {user['nama_toko']}")
        st.write(f"Logged in as: **@{user['username']}**")
        st.markdown("---")
        
        menu = st.radio(
            "Navigasi Menu:",
            ["🛒 Kasir Penjualan", "📦 Kelola Produk", "💸 Catatan Utang / Kasbon"]
        )
        
        st.markdown("---")
        if st.button("🚪 Keluar Akun (Logout)", use_container_width=True, type="secondary"):
            st.session_state.user_session = None
            st.session_state.keranjang = []
            st.rerun()

    # --- MENU 1: KASIR PENJUALAN ---
    if menu == "🛒 Kasir Penjualan":
        st.title("🛒 Kasir Penjualan")
        st.write("Kelola transaksi pembelian pelanggan dengan mudah secara langsung.")
        
        daftar_barang = ambil_produk(user["id"])
        
        if not daftar_barang:
            st.info("Produk Anda masih kosong. Silakan masuk ke menu **📦 Kelola Produk** untuk menambahkan produk jualan Anda terlebih dahulu!")
        else:
            col_kiri, col_kanan = st.columns([3, 2])
            
            with col_kiri:
                st.subheader("Pilih Produk")
                # Format pilihan produk untuk dropdown
                opsi_produk = {
                    f"{b['nama_produk']} (Stok: {b['stok']} | Rp{b['harga']:,})": b 
                    for b in daftar_barang if b['stok'] > 0
                }
                
                if opsi_produk:
                    pilihan = st.selectbox("Cari & Pilih Produk:", list(opsi_produk.keys()))
                    produk_terpilih = opsi_produk[pilihan]
                    
                    col_stok1, col_stok2 = st.columns(2)
                    with col_stok1:
                        jumlah = st.number_input("Jumlah Beli:", min_value=1, max_value=int(produk_terpilih['stok']), value=1)
                    with col_stok2:
                        st.write("")
                        st.write("")
                        tambah_btn = st.button("➕ Tambah ke Keranjang", use_container_width=True)
                        
                    if tambah_btn:
                        # Cek apakah barang sudah ada di keranjang
                        exists = False
                        for item in st.session_state.keranjang:
                            if item["id"] == produk_terpilih["id"]:
                                if item["jumlah"] + jumlah <= produk_terpilih["stok"]:
                                    item["jumlah"] += jumlah
                                    exists = True
                                    st.success(f"Jumlah {produk_terpilih['nama_produk']} di keranjang berhasil diperbarui!")
                                else:
                                    st.error(f"Stok tidak mencukupi untuk menambah jumlah tersebut!")
                                    exists = True
                                    
                        if not exists:
                            st.session_state.keranjang.append({
                                "id": produk_terpilih["id"],
                                "nama_produk": produk_terpilih["nama_produk"],
                                "harga": produk_terpilih["harga"],
                                "jumlah": jumlah,
                                "stok_maks": produk_terpilih["stok"]
                            })
                            st.success(f"{produk_terpilih['nama_produk']} ditambahkan ke keranjang!")
                            st.rerun()
                else:
                    st.warning("Semua stok produk Anda saat ini sedang kosong!")
            
            with col_kanan:
                st.subheader("📋 Keranjang Belanja")
                
                if not st.session_state.keranjang:
                    st.write("*Keranjang kosong*")
                else:
                    df_keranjang = pd.DataFrame(st.session_state.keranjang)
                    df_keranjang["Subtotal"] = df_keranjang["harga"] * df_keranjang["jumlah"]
                    
                    # Tampilkan tabel keranjang sederhana
                    for idx, item in enumerate(st.session_state.keranjang):
                        col_item1, col_item2, col_item3 = st.columns([3, 1, 1])
                        col_item1.write(f"**{item['nama_produk']}**<br>Rp{item['harga']:,} x {item['jumlah']}", unsafe_allow_html=True)
                        col_item2.write(f"**Rp{item['harga']*item['jumlah']:,}**")
                        if col_item3.button("❌", key=f"del_{idx}"):
                            st.session_state.keranjang.pop(idx)
                            st.rerun()
                            
                    total_harga = sum(item["harga"] * item["jumlah"] for item in st.session_state.keranjang)
                    st.markdown("---")
                    st.markdown(f"### Total Belanja: <span style='color:#2E7D32;'>Rp {total_harga: gentleman}</span>", unsafe_allow_html=True)
                    
                    # Pilihan Metode Pembayaran
                    metode_bayar = st.radio("Metode Pembayaran:", ["Tunai", "Utang / Kasbon"])
                    
                    if metode_bayar == "Tunai":
                        nominal_bayar = st.number_input("Nominal Uang Bayar (Rp):", min_value=0, value=total_harga)
                        kembalian = nominal_bayar - total_harga
                        
                        if kembalian >= 0:
                            st.info(f"Kembalian: **Rp {kembalian:,}**")
                        else:
                            st.error("Uang yang dimasukkan kurang!")
                            
                        if st.button("🔥 Selesaikan Transaksi Tunai", type="primary", use_container_width=True):
                            if nominal_bayar >= total_harga:
                                # Kurangi stok produk di database
                                for item in st.session_state.keranjang:
                                    update_stok(item["id"], item["stok_maks"] - item["jumlah"])
                                
                                st.balloons()
                                st.success("Transaksi Sukses! Stok produk telah otomatis diperbarui.")
                                st.session_state.keranjang = []
                                st.rerun()
                                
                    elif metode_bayar == "Utang / Kasbon":
                        nama_pembeli_utang = st.text_input("Nama Pelanggan yang Berutang:")
                        
                        if st.button("📌 Catat Sebagai Utang", type="primary", use_container_width=True):
                            if nama_pembeli_utang:
                                # Masukkan catatan ke tabel utang
                                if tambah_utang(user["id"], nama_pembeli_utang, total_harga):
                                    # Kurangi stok produk
                                    for item in st.session_state.keranjang:
                                        update_stok(item["id"], item["stok_maks"] - item["jumlah"])
                                        
                                    st.success(f"Transaksi dicatat sebagai utang atas nama **{nama_pembeli_utang}**!")
                                    st.session_state.keranjang = []
                                    st.rerun()
                            else:
                                st.warning("Masukkan nama pelanggan untuk mencatat utang!")


    # --- MENU 2: KELOLA PRODUK ---
    elif menu == "📦 Kelola Produk":
        st.title("📦 Kelola Produk Jualan")
        st.write("Tambahkan, ubah, atau hapus produk jualan toko Anda di sini.")
        
        tab_tambah, tab_daftar_barang = st.tabs(["➕ Tambah Produk Baru", "📋 Daftar Produk Toko Anda"])
        
        with tab_tambah:
            st.subheader("Formulir Produk Baru")
            new_nama = st.text_input("Nama Produk:", placeholder="Contoh: Beras Ramos 5Kg")
            new_harga = st.number_input("Harga Jual (Rp):", min_value=0, value=0, step=500)
            new_stok = st.number_input("Stok Awal Barang:", min_value=0, value=0, step=1)
            new_kode = st.text_input("Kode Produk / Barcode (Opsional):", placeholder="Contoh: BRG-001")
            
            if st.button("Simpan Produk", type="primary"):
                if new_nama and new_harga > 0:
                    if tambah_produk(user["id"], new_nama, new_harga, new_stok, new_kode):
                        st.success(f"Produk '{new_nama}' berhasil dimasukkan ke etalase toko!")
                        st.rerun()
                else:
                    st.warning("Nama produk dan Harga jual wajib diisi secara benar!")
                    
        with tab_daftar_barang:
            st.subheader("Data Semua Produk Jualan")
            semua_produk = ambil_produk(user["id"])
            
            if not semua_produk:
                st.info("Belum ada produk terdaftar.")
            else:
                df_tampil = pd.DataFrame(semua_produk)
                # Rapikan kolom tabel untuk user
                df_tampil = df_tampil.rename(columns={
                    "nama_produk": "Nama Produk",
                    "harga": "Harga (Rp)",
                    "stok": "Sisa Stok",
                    "kode_produk": "Kode Barang"
                })
                
                # Tampilkan tabel produk
                st.dataframe(df_tampil[["Nama Produk", "Harga (Rp)", "Sisa Stok", "Kode Barang"]], use_container_width=True)
                
                st.markdown("---")
                st.subheader("⚙️ Aksi Cepat Produk")
                
                # Pilihan edit stok cepat
                produk_pilihan_opsi = {p["nama_produk"]: p for p in semua_produk}
                pilih_edit = st.selectbox("Pilih Produk yang Ingin Diedit / Dihapus:", list(produk_pilihan_opsi.keys()))
                prod_data = produk_pilihan_opsi[pilih_edit]
                
                col_act1, col_act2 = st.columns(2)
                with col_act1:
                    st.markdown(f"**Ubah Stok Barang**")
                    stok_edit_val = st.number_input("Atur Stok Baru:", min_value=0, value=int(prod_data["stok"]))
                    if st.button("💾 Simpan Stok Baru", use_container_width=True):
                        update_stok(prod_data["id"], stok_edit_val)
                        st.success(f"Stok produk '{prod_data['nama_produk']}' berhasil diubah!")
                        st.rerun()
                        
                with col_act2:
                    st.markdown("**Hapus Produk**")
                    st.write("Aksi ini tidak bisa dibatalkan.")
                    if st.button("🗑️ Hapus Produk Permanen", type="secondary", use_container_width=True):
                        if hapus_produk(prod_data["id"]):
                            st.success("Produk berhasil dihapus dari etalase toko!")
                            st.rerun()


    # --- MENU 3: CATATAN UTANG ---
    elif menu == "💸 Catatan Utang / Kasbon":
        st.title("💸 Buku Catatan Utang & Kasbon")
        st.write("Pantau dan catat transaksi utang piutang pelanggan toko Anda.")
        
        col_utang1, col_utang2 = st.columns([3, 2])
        
        with col_utang1:
            st.subheader("Daftar Piutang Pelanggan")
            list_utang = ambil_utang(user["id"])
            
            if not list_utang:
                st.info("Hebat! Saat ini tidak ada pelanggan yang tercatat memiliki utang di toko Anda. 🎉")
            else:
                df_utang = pd.DataFrame(list_utang)
                df_utang["tanggal_utang"] = pd.to_datetime(df_utang["tanggal_utang"]).dt.strftime('%d %B %Y')
                
                for idx, row in df_utang.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div style="background-color: #f9f9f9; padding: 15px; border-radius: 8px; border-left: 5px solid #d32f2f; margin-bottom: 10px;">
                            <span style="font-size: 1.15rem; font-weight: bold; color: #333;">{row['nama_pelanggan']}</span><br>
                            <span style="color: #c62828; font-weight: bold; font-size: 1.1rem;">Sisa Utang: Rp {row['sisa_utang']:,}</span><br>
                            <span style="color: #777; font-size: 0.85rem;">Tanggal Berutang: {row['tanggal_utang']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Tombol cicil utang cepat
                        with st.expander(f"Bayar / Cicil Utang {row['nama_pelanggan']}"):
                            bayar_nom = st.number_input("Nominal Bayar (Rp):", min_value=1, max_value=int(row['sisa_utang']), value=int(row['sisa_utang']), key=f"pay_val_{row['id']}")
                            if st.button("Konfirmasi Pembayaran", key=f"pay_btn_{row['id']}", type="primary"):
                                if bayar_utang_db(row['id'], bayar_nom, row['sisa_utang']):
                                    st.success(f"Pembayaran utang sebesar Rp{bayar_nom:,} berhasil disimpan!")
                                    st.rerun()
                                    
        with col_utang2:
            st.subheader("➕ Catat Utang Baru Manual")
            st.write("Gunakan menu ini jika Anda ingin mencatat utang secara manual tanpa melalui transaksi kasir penjualan.")
            
            u_nama = st.text_input("Nama Lengkap Pelanggan:", placeholder="Contoh: Pak Budi")
            u_nominal = st.number_input("Nominal Utang (Rp):", min_value=0, value=0, step=1000)
            
            if st.button("Simpan Catatan Utang", use_container_width=True):
                if u_nama and u_nominal > 0:
                    if tambah_utang(user["id"], u_nama, u_nominal):
                        st.success(f"Utang atas nama **{u_nama}** sebesar **Rp{u_nominal:,}** sukses dicatat!")
                        st.rerun()
                else:
                    st.warning("Nama pelanggan dan Nominal utang harus diisi dengan benar!")
