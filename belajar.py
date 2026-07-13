import os
import pandas as pd
from datetime import datetime

FILE_EXCEL = "laporan_keuangan_2026_07.xlsx"
FILE_STOK = "stok_barang.xlsx"
FILE_CONFIG = "pengaturan_toko.txt"

def dapatkan_nama_toko():
    if os.path.exists(FILE_CONFIG):
        with open(FILE_CONFIG, "r") as f:
            return f.read().strip()
    else:
        print("\n=======================================")
        print("     PENGATURAN AWAL APLIKASI KASIR")
        print("=======================================")
        nama = input("Masukkan Nama Toko Anda (Cukup ketik 1x saja): ").strip()
        if not nama:
            nama = "TOKO KASIR"
        with open(FILE_CONFIG, "w") as f:
            f.write(nama)
        return nama

def ubah_nama_toko():
    nama_lama = dapatkan_nama_toko()
    print(f"\n=== UBAH NAMA TOKO ({nama_lama}) ===")
    nama_baru = input("Masukkan Nama Toko yang Baru: ").strip()
    if nama_baru:
        with open(FILE_CONFIG, "w") as f:
            f.write(nama_baru)
        print(f"✓ Sukses! Nama toko berhasil diganti menjadi: '{nama_baru}'")
    else:
        print("⚠️ Nama toko tidak boleh kosong. Perubahan dibatalkan.")

def inisialisasi_sistem():
    if not os.path.exists(FILE_EXCEL):
        kolom = [
            'Waktu', 'Nama Pembeli', 'Barang', 'Harga', 'Jml', 
            'Subtotal', 'Total Tran', 'Bayar/DP', 'Kembali', 'Status', 'Sisa Utang'
        ]
        pd.DataFrame(columns=kolom).to_excel(FILE_EXCEL, index=False)
        
    if not os.path.exists(FILE_STOK):
        kolom_stok = ['Nama Barang', 'Stok']
        pd.DataFrame(columns=kolom_stok).to_excel(FILE_STOK, index=False)

def lihat_semua_stok():
    nama_toko = dapatkan_nama_toko()
    print(f"\n=== DAFTAR SEMUA STOK GUDANG {nama_toko} ===")
    try:
        df_stok = pd.read_excel(FILE_STOK)
        if df_stok.empty:
            print("❌ Gudang kosong. Silakan tambah barang terlebih dahulu di Menu 3.")
            return False
            
        print(f"{'No':<4} | {'Nama Barang':<25} | {'Jumlah Stok':<10}")
        print("-" * 45)
        for idx, row in df_stok.iterrows():
            print(f"{idx+1:<4} | {row['Nama Barang']:<25} | {int(row['Stok']):<10} biji")
        print("-" * 45)
        return True
    except Exception:
        print("⚠️ Gagal membaca data stok. Pastikan file Excel closed.")
        return False

def cek_peringatan_stok():
    try:
        df_stok = pd.read_excel(FILE_STOK)
        df_stok['Stok'] = pd.to_numeric(df_stok['Stok'], errors='coerce').fillna(0)
        stok_kritis = df_stok[df_stok['Stok'] <= 5]
        
        if not df_stok.empty and not stok_kritis.empty:
            print("\n⚠️  [ALARM STOK GUDANG MINIM] - SEGERA KULAKAN BARANG INI:")
            for idx, row in stok_kritis.iterrows():
                print(f"   • Kritis! {row['Nama Barang']} sisa: {int(row['Stok'])} biji")
            print("-" * 50)
    except Exception:
        pass

def tambah_stok_barang():
    nama_toko = dapatkan_nama_toko()
    print(f"\n=== KULAKAN / TAMBAH STOK BARANG {nama_toko} ===")
    try:
        df_stok = pd.read_excel(FILE_STOK)
        barang = input("Masukkan Nama Barang: ").strip()
        if not barang: return
            
        jumlah_tambah = int(input(f"Masukkan Jumlah Stok Tambahan untuk '{barang}': "))
        
        mask = df_stok['Nama Barang'].astype(str).str.lower() == barang.lower()
        if df_stok[mask].empty:
            data_baru = {'Nama Barang': barang, 'Stok': jumlah_tambah}
            df_stok = pd.concat([df_stok, pd.DataFrame([data_baru])], ignore_index=True)
            print(f"✓ Berhasil mendaftarkan produk BARU: '{barang}' sejumlah {jumlah_tambah} biji.")
        else:
            nama_asli_gudang = df_stok.loc[mask, 'Nama Barang'].values[0]
            df_stok.loc[mask, 'Stok'] += jumlah_tambah
            print(f"✓ Stok '{nama_asli_gudang}' otomatis ditambahkan di gudang!")
            
        df_stok.to_excel(FILE_STOK, index=False)
    except Exception as e:
        print(f"⚠️ Gagal memperbarui stok. Pastikan Excel closed.")

def hapus_barang_gudang():
    nama_toko = dapatkan_nama_toko()
    print(f"\n=== HAPUS BARANG DARI GUDANG {nama_toko} ===")
    try:
        ada_barang = lihat_semua_stok()
        if not ada_barang:
            return
            
        input_hapus = input("Masukkan Nomor atau Nama Barang yang ingin DIHAPUS: ").strip()
        if not input_hapus:
            return
            
        df_stok = pd.read_excel(FILE_STOK)
        mask = pd.Series([False] * len(df_stok))
        nama_asli = ""

        # Cek apakah input berupa NOMOR (angka)
        if input_hapus.isdigit():
            no_index = int(input_hapus) - 1
            if 0 <= no_index < len(df_stok):
                mask.iloc[no_index] = True
                nama_asli = df_stok.iloc[no_index]['Nama Barang']
            else:
                print(f"⚠️ Nomor urut {input_hapus} tidak ada dalam daftar.")
                return
        else:
            # Jika input berupa NAMA BARANG
            mask = df_stok['Nama Barang'].astype(str).str.lower() == input_hapus.lower()
            if df_stok[mask].empty:
                print(f"⚠️ Barang '{input_hapus}' tidak ditemukan.")
                return
            nama_asli = df_stok.loc[mask, 'Nama Barang'].values[0]

        # Konfirmasi penghapusan
        yakin = input(f"Apakah Anda yakin ingin menghapus '{nama_asli}' secara permanen? (y/n): ").strip().lower()
        if yakin == 'y':
            df_stok = df_stok[~mask]
            df_stok.to_excel(FILE_STOK, index=False)
            print(f"✓ Sukses! Produk '{nama_asli}' telah dihapus dari sistem gudang.")
        else:
            print("Proses penghapusan dibatalkan.")
            
    except Exception as e:
        print("⚠️ Gagal menghapus barang. Pastikan file 'stok_barang.xlsx' sedang ditutup.")

def buat_dan_cetak_struk(waktu, nama, barang, harga, jml, total, bayar, kembali, status, sisa_utang):
    nama_toko = dapatkan_nama_toko()
    isi_struk = []
    isi_struk.append("="*42)
    isi_struk.append(f"{nama_toko.center(42)}")
    isi_struk.append("Nota Bukti Transaksi Resmi Penjualan".center(42))
    isi_struk.append("="*42)
    isi_struk.append(f" Waktu   : {waktu}")
    isi_struk.append(f" Pelanggan : {nama}")
    isi_struk.append("-"*42)
    isi_struk.append(f" Detail Item:")
    isi_struk.append(f" - {barang:<18} {jml:>2} x Rp {harga:,}".replace(",", "."))
    isi_struk.append("-"*42)
    isi_struk.append(f" TOTAL BELANJA : Rp {total:,}".replace(",", "."))
    isi_struk.append(f" UANG TUNAI    : Rp {bayar:,}".replace(",", "."))
    isi_struk.append(f" KEMBALIAN     : Rp {kembali:,}".replace(",", "."))
    isi_struk.append("-"*42)
    isi_struk.append(f" STATUS NOTA   : {status}")
    if sisa_utang > 0:
        isi_struk.append(f" SISA UTANG    : Rp {sisa_utang:,}".replace(",", "."))
    isi_struk.append("="*42)
    isi_struk.append("Terima Kasih Atas Kunjungan Anda!".center(42))
    isi_struk.append("="*42)
    
    teks_utuh = "\n".join(isi_struk)
    print("\n" + teks_utuh)
    print("\n💡 Tips: Blok teks nota di atas, tekan Ctrl+C untuk menyalin dan kirim lewat WA manual.")

def tambah_transaksi_baru():
    print("\n=== INPUT TRANSAKSI PENJUALAN BARU ===")
    try:
        df_stok = pd.read_excel(FILE_STOK)
        nama = input("Nama Pembeli: ").strip()
        barang = input("Nama Barang: ").strip()
        
        mask_stok = df_stok['Nama Barang'].astype(str).str.lower() == barang.lower()
        if df_stok[mask_stok].empty:
            print(f"⚠️ Barang '{barang}' tidak ditemukan di gudang. Silakan daftarkan dulu di Menu 3.")
            return
            
        stok_sekarang = int(df_stok.loc[mask_stok, 'Stok'].values[0])
        jml = int(input(f"Jumlah Beli (Stok gudang saat ini {stok_sekarang} biji): "))
        
        if jml > stok_sekarang:
            print(f"❌ Transaksi Dibatalkan! Stok tidak mencukupi.")
            return
            
        harga_input = input("Harga Satuan (Bisa pakai titik): ").replace(".", "")
        harga = int(harga_input)
        
        subtotal = harga * jml
        total_tran = subtotal
        
        print(f"Total yang harus dibayar: Rp {total_tran:,}".replace(",", "."))
        bayar_input = input("Jumlah Uang yang Dibayar/DP (Bisa pakai titik): ").replace(".", "")
        bayar = int(bayar_input)
        
        selisih = bayar - total_tran
        if selisih >= 0:
            kembali = selisih
            sisa_utang = 0
            status = "LUNAS"
        else:
            kembali = 0
            sisa_utang = abs(selisih)
            status = "UTANG"
            
        waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        df_stok.loc[mask_stok, 'Stok'] -= jml
        df_stok.to_excel(FILE_STOK, index=False)
        
        df_transaksi = pd.read_excel(FILE_EXCEL)
        data_baru = {
            'Waktu': waktu_sekarang, 'Nama Pembeli': nama, 'Barang': barang, 'Harga': harga, 'Jml': jml,
            'Subtotal': subtotal, 'Total Tran': total_tran, 'Bayar/DP': bayar, 'Kembali': kembali,
            'Status': status, 'Sisa Utang': sisa_utang
        }
        df_transaksi = pd.concat([df_transaksi, pd.DataFrame([data_baru])], ignore_index=True)
        df_transaksi.to_excel(FILE_EXCEL, index=False)
        
        print("\n✓ Sukses! Transaksi disimpan dan stok otomatis terpotong.")
        buat_dan_cetak_struk(waktu_sekarang, nama, barang, harga, jml, total_tran, bayar, kembali, status, sisa_utang)
        
    except Exception as e:
        print(f"⚠️ Gagal memproses transaksi. Pastikan semua file Excel sudah ditutup.")

def proses_pelunasan_utang():
    print("\n=== INPUT PELUNASAN UTANG PELANGGAN ===")
    try:
        df = pd.read_excel(FILE_EXCEL)
        df['Sisa Utang'] = pd.to_numeric(df['Sisa Utang'], errors='coerce').fillna(0)
        daftar_utang = df[(df['Status'].astype(str).str.upper() == 'UTANG') & (df['Sisa Utang'] > 0)]
        
        if daftar_utang.empty:
            print("🎉 Kabar baik! Saat ini tidak ada pelanggan yang memiliki riwayat utang.")
            return
            
        print("-" * 50)
        print("DAFTAR PELANGGAN YANG MASIH MEMILIKI UTANG:")
        rekap_utang = daftar_utang.groupby('Nama Pembeli')['Sisa Utang'].sum().reset_index()
        for idx, row in rekap_utang.iterrows():
            total_utang_format = f"{int(row['Sisa Utang']):,}".replace(",", ".")
            print(f"- {row['Nama Pembeli']} (Sisa Utang: Rp {total_utang_format})")
        print("-" * 50)
        
        nama = input("Masukkan Nama Pembeli dari daftar di atas: ").strip()
        mask_utang = (df['Nama Pembeli'].astype(str).str.lower() == nama.lower()) & (df['Status'].astype(str).str.upper() == 'UTANG')
        
        if df[mask_utang].empty:
            print(f"⚠️ Data utang atas nama '{nama}' tidak ditemukan.")
            return
            
        jumlah_bayar_input = input(f"Masukkan nominal uang pembayaran utang dari {nama} (Bisa pakai titik): ").replace(".", "")
        jumlah_bayar = int(jumlah_bayar_input)
        
        df.loc[mask_utang, 'Sisa Utang'] = 0
        waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        data_pelunasan = {
            'Waktu': waktu_sekarang, 'Nama Pembeli': nama, 'Barang': 'Bayar Utang', 'Harga': 0, 'Jml': 0,
            'Subtotal': 0, 'Total Tran': jumlah_bayar, 'Bayar/DP': jumlah_bayar, 'Kembali': 0,
            'Status': 'PELUNASAN UTANG (LUNAS)', 'Sisa Utang': 0
        }
        
        df = pd.concat([df, pd.DataFrame([data_pelunasan])], ignore_index=True)
        df.to_excel(FILE_EXCEL, index=False)
        print(f"✓ Sukses! Utang lama {nama} dibersihkan.")
        buat_dan_cetak_struk(waktu_sekarang, nama, "Pelunasan Utang", 0, 0, jumlah_bayar, jumlah_bayar, 0, "LUNAS", 0)
    except Exception as e:
        print(f"⚠️ Gagal memproses pelunasan.")

def menu_utama():
    inisialisasi_sistem()
    while True:
        nama_toko = dapatkan_nama_toko()
        cek_peringatan_stok() 
        print("\n=======================================")
        print(f"   {nama_toko.center(33)}")
        print("=======================================")
        print("1. Input Penjualan Baru & Potong Stok")
        print("2. Input Pelunasan Utang")
        print("3. Tambah / Kulakan Stok Gudang")
        print("4. Lihat Semua Stok Gudang")
        print("5. Hapus Barang dari Gudang")
        print("6. Ubah Nama Toko")
        print("7. Keluar Aplikasi")
        pilihan = input("Pilih menu (1/2/3/4/5/6/7): ").strip()
        
        if pilihan == '1':
            tambah_transaksi_baru()
        elif pilihan == '2':
            proses_pelunasan_utang()
        elif pilihan == '3':
            tambah_stok_barang()
        elif pilihan == '4':
            lihat_semua_stok()
        elif pilihan == '5':
            hapus_barang_gudang()
        elif pilihan == '6':
            ubah_nama_toko()
        elif pilihan == '7':
            print("Aplikasi ditutup. Selamat beristirahat!")
            break

if __name__ == "__main__":
    menu_utama()