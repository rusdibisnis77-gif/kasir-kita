from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import streamlit as st
GOOGLE_CLIENT_ID = "384215012630-32l3aunigm1qou39g43ta4jkaq8cie3u.apps.googleusercontent.com"

st.set_page_config(
    page_title="Sistem Kasir Pintar Modern",
    page_icon="🏪",
    layout="wide",
)


BASE_DIR = Path(__file__).resolve().parent
FILE_EXCEL = BASE_DIR / "laporan_keuangan_2026_07.xlsx"
FILE_STOK = BASE_DIR / "stok_barang.xlsx"
FILE_CONFIG = BASE_DIR / "pengaturan_toko.txt"

KOLOM_TRANSAKSI = [
    "Waktu",
    "Nama Pembeli",
    "Barang Belanjaan",
    "Total Belanja",
    "Bayar/DP",
    "Kembali",
    "Status",
    "Sisa Utang",
]
KOLOM_STOK = ["Nama Barang", "Harga Satuan", "Stok"]


def rupiah(nilai: float | int) -> str:
    return f"Rp {int(nilai):,}".replace(",", ".")


def muat_excel(path: Path, kolom: List[str]) -> pd.DataFrame:
    if not path.exists():
        df = pd.DataFrame(columns=kolom)
        df.to_excel(path, index=False)
        return df

    df = pd.read_excel(path)
    for nama_kolom in kolom:
        if nama_kolom not in df.columns:
            df[nama_kolom] = None
    return df[kolom]


def simpan_excel(df: pd.DataFrame, path: Path) -> None:
    df.to_excel(path, index=False)


def inisialisasi_sistem() -> None:
    if not FILE_EXCEL.exists():
        df_transaksi = pd.DataFrame(columns=KOLOM_TRANSAKSI)
        df_transaksi.to_excel(FILE_EXCEL, index=False)
    else:
        muat_excel(FILE_EXCEL, KOLOM_TRANSAKSI)
        
    if not FILE_STOK.exists():
        df_stok = pd.DataFrame(columns=KOLOM_STOK)
        df_stok.to_excel(FILE_STOK, index=False)
    else:
        muat_excel(FILE_STOK, KOLOM_STOK)
        
    if not FILE_CONFIG.exists():
        FILE_CONFIG.write_text("TOKO KASIR PINTAR", encoding="utf-8")


def dapatkan_nama_toko() -> str:
    try:
        nama = FILE_CONFIG.read_text(encoding="utf-8").strip()
        return nama or "TOKO KASIR PINTAR"
    except OSError:
        return "TOKO KASIR PINTAR"


def simpan_nama_toko(nama_baru: str) -> None:
    FILE_CONFIG.write_text(nama_baru.strip(), encoding="utf-8")


def muat_stok() -> pd.DataFrame:
    df = muat_excel(FILE_STOK, KOLOM_STOK).copy()
    if df.empty:
        return df
    df["Nama Barang"] = df["Nama Barang"].astype(str).str.strip()
    df["Harga Satuan"] = pd.to_numeric(df["Harga Satuan"], errors="coerce").fillna(0).astype(int)
    df["Stok"] = pd.to_numeric(df["Stok"], errors="coerce").fillna(0).astype(int)
    df = df[df["Nama Barang"] != ""].reset_index(drop=True)
    return df


def muat_transaksi() -> pd.DataFrame:
    df = muat_excel(FILE_EXCEL, KOLOM_TRANSAKSI).copy()
    if df.empty:
        return df
    angka = ["Total Belanja", "Bayar/DP", "Kembali", "Sisa Utang"]
    for kolom in angka:
        df[kolom] = pd.to_numeric(df[kolom], errors="coerce").fillna(0).astype(int)
    df["Nama Pembeli"] = df["Nama Pembeli"].astype(str).fillna("").str.strip()
    df["Status"] = df["Status"].astype(str).fillna("").str.strip()
    df["Barang Belanjaan"] = df["Barang Belanjaan"].astype(str).fillna("").str.strip()
    return df


def stok_kritis(df_stok: pd.DataFrame, batas: int = 5) -> pd.DataFrame:
    if df_stok.empty:
        return df_stok
    return df_stok[df_stok["Stok"] <= batas].copy()


def buat_teks_belanjaan(keranjang: List[dict]) -> str:
    return ", ".join(f"{item['barang']} ({item['jumlah']}x)" for item in keranjang)


def buat_nota(
    nama_toko: str,
    waktu: str,
    pelanggan: str,
    keranjang: List[dict],
    total: int,
    bayar: int,
    kembali: int,
    status: str,
    sisa_utang: int,
) -> str:
    detail = "\n".join(
        f"- {item['barang'][:18]:<18} {item['jumlah']:>2}x  {rupiah(item['subtotal'])}"
        for item in keranjang
    )
    sisa_text = f"SISA UTANG    : {rupiah(sisa_utang)}\n" if sisa_utang > 0 else ""
    return (
        "==========================================\n"
        f"{nama_toko.center(42)}\n"
        "==========================================\n"
        f"Waktu     : {waktu}\n"
        f"Pelanggan : {pelanggan}\n"
        "------------------------------------------\n"
        "Detail Belanja:\n"
        f"{detail}\n"
        "------------------------------------------\n"
        f"GRAND TOTAL   : {rupiah(total)}\n"
        f"UANG TUNAI    : {rupiah(bayar)}\n"
        f"KEMBALIAN     : {rupiah(kembali)}\n"
        "------------------------------------------\n"
        f"STATUS TRAN   : {status}\n"
        f"{sisa_text}"
        "==========================================\n"
        " Terima Kasih Atas Kunjungan Anda!\n"
        "=========================================="
    )


def hitung_ringkasan(df_transaksi: pd.DataFrame) -> Tuple[int, int, int, int]:
    if df_transaksi.empty:
        return 0, 0, 0, 0
    total_transaksi = len(df_transaksi[df_transaksi["Total Belanja"] > 0])
    omzet = int(df_transaksi["Bayar/DP"].sum())
    total_utang = int(df_transaksi["Sisa Utang"].sum())
    jumlah_pelanggan_utang = int(
        df_transaksi[df_transaksi["Sisa Utang"] > 0]["Nama Pembeli"].nunique()
    )
    return total_transaksi, omzet, total_utang, jumlah_pelanggan_utang


def tambah_ke_keranjang(df_stok: pd.DataFrame, nama_barang: str, jumlah: int) -> Tuple[bool, str]:
    stok_baris = df_stok[df_stok["Nama Barang"] == nama_barang]
    if stok_baris.empty:
        return False, "Produk tidak ditemukan di gudang."

    info_barang = stok_baris.iloc[0]
    stok_tersedia = int(info_barang["Stok"])
    harga = int(info_barang["Harga Satuan"])

    if jumlah <= 0:
        return False, "Jumlah beli harus lebih dari 0."
    if jumlah > stok_tersedia:
        return False, "Jumlah beli melebihi stok gudang."

    for item in st.session_state.keranjang:
        if item["barang"] == nama_barang:
            total_baru = item["jumlah"] + jumlah
            if total_baru > stok_tersedia:
                return False, "Total barang di keranjang melebihi stok gudang."
            item["jumlah"] = total_baru
            item["subtotal"] = item["jumlah"] * item["harga"]
            return True, f"{nama_barang} berhasil diperbarui di keranjang."

    st.session_state.keranjang.append(
        {
            "barang": nama_barang,
            "harga": harga,
            "jumlah": int(jumlah),
            "subtotal": int(harga * jumlah),
        }
    )
    return True, f"{nama_barang} berhasil ditambahkan ke keranjang."


def hapus_item_keranjang(nama_barang: str) -> None:
    st.session_state.keranjang = [
        item for item in st.session_state.keranjang if item["barang"] != nama_barang
    ]


def proses_transaksi(
    nama_pembeli: str,
    uang_bayar: int,
    df_stok: pd.DataFrame,
    df_transaksi: pd.DataFrame,
    nama_toko: str,
) -> Tuple[bool, str, str]:
    if not nama_pembeli.strip():
        return False, "Nama pembeli wajib diisi terlebih dahulu.", ""
    if not st.session_state.keranjang:
        return False, "Keranjang masih kosong.", ""

    total_belanja = sum(item["subtotal"] for item in st.session_state.keranjang)
    waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    selisih = int(uang_bayar) - int(total_belanja)
    status = "LUNAS" if selisih >= 0 else "UTANG"
    kembali = max(selisih, 0)
    sisa_utang = abs(selisih) if selisih < 0 else 0

    stok_terbaru = df_stok.copy()
    for item in st.session_state.keranjang:
        mask = stok_terbaru["Nama Barang"] == item["barang"]
        stok_sekarang = int(stok_terbaru.loc[mask, "Stok"].iloc[0])
        if item["jumlah"] > stok_sekarang:
            return False, f"Stok {item['barang']} sudah berubah. Silakan cek ulang keranjang.", ""
        stok_terbaru.loc[mask, "Stok"] = stok_sekarang - int(item["jumlah"])

    data_baru = {
        "Waktu": waktu_sekarang,
        "Nama Pembeli": nama_pembeli.strip(),
        "Barang Belanjaan": buat_teks_belanjaan(st.session_state.keranjang),
        "Total Belanja": int(total_belanja),
        "Bayar/DP": int(uang_bayar),
        "Kembali": int(kembali),
        "Status": status,
        "Sisa Utang": int(sisa_utang),
    }

    transaksi_terbaru = pd.concat(
        [df_transaksi, pd.DataFrame([data_baru])], ignore_index=True
    )
    simpan_excel(stok_terbaru, FILE_STOK)
    simpan_excel(transaksi_terbaru, FILE_EXCEL)

    nota = buat_nota(
        nama_toko=nama_toko,
        waktu=waktu_sekarang,
        pelanggan=nama_pembeli.strip(),
        keranjang=st.session_state.keranjang,
        total=int(total_belanja),
        bayar=int(uang_bayar),
        kembali=int(kembali),
        status=status,
        sisa_utang=int(sisa_utang),
    )
    return True, "Transaksi berhasil disimpan.", nota


def distribusikan_pembayaran_utang(df_keuangan: pd.DataFrame, nama_pelanggan: str, bayar: int) -> Tuple[pd.DataFrame, int]:
    df = df_keuangan.copy()
    mask = (df["Nama Pembeli"] == nama_pelanggan) & (df["Sisa Utang"] > 0)
    indeks_utang = df[mask].index.tolist()
    sisa_bayar = int(bayar)

    for idx in indeks_utang:
        utang = int(df.at[idx, "Sisa Utang"])
        if sisa_bayar <= 0:
            break
        terbayar = min(utang, sisa_bayar)
        sisa_utangnya = utang - terbayar
        df.at[idx, "Sisa Utang"] = sisa_utangnya
        df.at[idx, "Status"] = "LUNAS" if sisa_utangnya == 0 else "UTANG"
        sisa_bayar -= terbayar

    return df, sisa_bayar


inisialisasi_sistem()

if "keranjang" not in st.session_state:
    st.session_state.keranjang = []
if "pembeli_sekarang" not in st.session_state:
    st.session_state.pembeli_sekarang = ""
if "nota_terakhir" not in st.session_state:
    st.session_state.nota_terakhir = ""

nama_toko = dapatkan_nama_toko()
df_stok = muat_stok()
df_transaksi = muat_transaksi()

st.title(f"🏪 {nama_toko}")
st.caption("Sistem kasir modern yang sederhana, rapi, dan mudah dipakai oleh semua operator toko.")

total_transaksi, omzet, total_utang, jumlah_pelanggan_utang = hitung_ringkasan(df_transaksi)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Transaksi", total_transaksi)
col2.metric("Kas Masuk", rupiah(omzet))
col3.metric("Sisa Utang", rupiah(total_utang))
col4.metric("Pelanggan Berutang", jumlah_pelanggan_utang)

stok_alert = stok_kritis(df_stok)
if not stok_alert.empty:
    daftar_alert = ", ".join(
        f"{row['Nama Barang']} ({int(row['Stok'])} sisa)"
        for _, row in stok_alert.iterrows()
    )
    st.warning(f"Stok minim terdeteksi: {daftar_alert}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "🛒 Kasir",
        "💳 Pelunasan Utang",
        "📥 Kelola Barang",
        "📦 Stok Gudang",
        "⚙️ Pengaturan",
    ]
)


with tab1:
    st.subheader("Transaksi Penjualan")
    st.write("Ikuti 3 langkah berikut: isi pelanggan, masukkan barang ke keranjang, lalu proses pembayaran.")

    if df_stok.empty:
        st.info("Gudang masih kosong. Tambahkan produk terlebih dahulu di tab `Kelola Barang`.")
    else:
        kiri, kanan = st.columns([1.1, 1])

        with kiri:
            st.markdown("### 1. Data Pelanggan")
            nama_input = st.text_input(
                "Nama pembeli",
                value=st.session_state.pembeli_sekarang,
                placeholder="Contoh: Bapak Andi",
            )
            st.session_state.pembeli_sekarang = nama_input

            st.markdown("### 2. Tambah Barang")
            
            daftar_produk = df_stok["Nama Barang"].tolist()
            barang_terpilih = st.selectbox("Pilih produk", daftar_produk, key="sb_barang_terpilih")
            
            # Mengunci baris info barang secara akurat berdasarkan Nama Barang yang sedang dipilih
            info_barang = df_stok[df_stok["Nama Barang"] == barang_terpilih].iloc[0]
            stok_gudang_asli = int(info_barang["Stok"])
            
            # Hitung jumlah barang ini yang sudah masuk di antrean keranjang belanja
            jumlah_di_keranjang = sum(item["jumlah"] for item in st.session_state.keranjang if item["barang"] == barang_terpilih)
            stok_aman_tersisa = max(0, stok_gudang_asli - jumlah_di_keranjang)

            # Bagian Input Jumlah Beli
            jumlah_beli = st.number_input(
                "Jumlah beli",
                min_value=1,
                max_value=max(1, stok_aman_tersisa),
                step=1,
                key="num_jumlah_beli"
            )
            
            # Hitung pengurangan langsung di layar secara Real-time berdasarkan angka Jumlah Beli yang sedang diketik
            stok_layar_realtime = max(0, stok_aman_tersisa - int(jumlah_beli))
            
            st.info(
                f"Harga: {rupiah(info_barang['Harga Satuan'])} | "
                f"Stok tersedia: {stok_layar_realtime}"
            )

            with st.form("form_tambah_keranjang", clear_on_submit=True):
                submit_tambah = st.form_submit_button("Tambah ke Keranjang", use_container_width=True)

                if submit_tambah:
                    sukses, pesan = tambah_ke_keranjang(df_stok, barang_terpilih, int(jumlah_beli))
                    if sukses:
                        st.success(pesan)
                        st.rerun()
                    else:
                        st.error(pesan)

        with kanan:
            st.markdown("### 3. Ringkasan Belanja")
            if not st.session_state.keranjang:
                st.info("Keranjang masih kosong.")
            else:
                df_keranjang = pd.DataFrame(st.session_state.keranjang)
                df_keranjang = df_keranjang.rename(
                    columns={
                        "barang": "Nama Barang",
                        "harga": "Harga Satuan",
                        "jumlah": "Jumlah",
                        "subtotal": "Subtotal",
                    }
                )
                st.dataframe(
                    df_keranjang,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Harga Satuan": st.column_config.NumberColumn(format="Rp %d"),
                        "Subtotal": st.column_config.NumberColumn(format="Rp %d"),
                    },
                )

                total_harus_dibayar = int(df_keranjang["Subtotal"].sum())
                st.metric("Total Belanja", rupiah(total_harus_dibayar))

                with st.form("form_hapus_item"):
                    item_dihapus = st.selectbox(
                        "Hapus item dari keranjang",
                        df_keranjang["Nama Barang"].tolist(),
                    )
                    submit_hapus = st.form_submit_button("Hapus Item")
                    if submit_hapus:
                        hapus_item_keranjang(item_dihapus)
                        st.rerun()

                col_reset, col_bayar = st.columns([1, 1.4])
                with col_reset:
                    if st.button("Kosongkan Keranjang", use_container_width=True):
                        st.session_state.keranjang = []
                        st.rerun()
                with col_bayar:
                    with st.form("form_pembayaran"):
                        uang_bayar = st.number_input(
                            "Uang tunai / DP",
                            min_value=0,
                            step=1000,
                        )
                        submit_bayar = st.form_submit_button(
                            "Proses dan Simpan Transaksi",
                            use_container_width=True,
                            type="primary",
                        )

                        if submit_bayar:
                            berhasil, pesan, nota = proses_transaksi(
                                nama_pembeli=nama_input,
                                uang_bayar=int(uang_bayar),
                                df_stok=df_stok,
                                df_transaksi=df_transaksi,
                                nama_toko=nama_toko,
                            )
                            if berhasil:
                                st.session_state.nota_terakhir = nota
                                st.session_state.keranjang = []
                                st.session_state.pembeli_sekarang = ""
                                st.success(pesan)
                                st.rerun()
                            else:
                                st.error(pesan)

    if st.session_state.nota_terakhir:
        st.write("---")
        st.subheader("Nota Terakhir")
        st.code(st.session_state.nota_terakhir, language="text")
        st.caption("Nota ini bisa langsung disalin dan dikirim ke pelanggan melalui WhatsApp.")


with tab2:
    st.subheader("Pelunasan Utang Pelanggan")
    if df_transaksi.empty or "Sisa Utang" not in df_transaksi.columns:
        st.info("Belum ada catatan transaksi utang.")
    else:
        daftar_utang = (
            df_transaksi[df_transaksi["Sisa Utang"] > 0]
            .groupby("Nama Pembeli", as_index=False)["Sisa Utang"]
            .sum()
            .sort_values(by="Nama Pembeli")
        )

        if daftar_utang.empty:
            st.success("Semua utang pelanggan sudah lunas.")
        else:
            st.dataframe(
                daftar_utang,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Nama Pembeli": "Nama Pembeli",
                    "Sisa Utang": st.column_config.NumberColumn(format="Rp %d"),
                },
            )

            with st.form("form_pelunasan"):
                nama_pelanggan = st.selectbox(
                    "Pilih pelanggan",
                    daftar_utang["Nama Pembeli"].tolist(),
                )
                total_utang_pelanggan = int(
                    daftar_utang.loc[
                        daftar_utang["Nama Pembeli"] == nama_pelanggan, "Sisa Utang"
                    ].iloc[0]
                )
                st.warning(f"Total utang saat ini: {rupiah(total_utang_pelanggan)}")
                nominal_bayar = st.number_input(
                    "Nominal pembayaran",
                    min_value=1,
                    step=1000,
                )
                simpan_pelunasan = st.form_submit_button("Simpan Pelunasan", type="primary")

                if simpan_pelunasan:
                    if nominal_bayar > total_utang_pelanggan:
                        st.error("Nominal pembayaran melebihi total utang pelanggan.")
                    else:
                        df_baru, sisa_bayar = distribusikan_pembayaran_utang(
                            df_transaksi,
                            nama_pelanggan,
                            int(nominal_bayar),
                        )

                        waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        status_pelunasan = (
                            "PELUNASAN UTANG (LUNAS)"
                            if nominal_bayar == total_utang_pelanggan
                            else "PELUNASAN UTANG (SEBAGIAN)"
                        )
                        catatan_pelunasan = {
                            "Waktu": waktu_sekarang,
                            "Nama Pembeli": nama_pelanggan,
                            "Barang Belanjaan": "Setor Bayar Utang",
                            "Total Belanja": 0,
                            "Bayar/DP": int(nominal_bayar),
                            "Kembali": 0,
                            "Status": status_pelunasan,
                            "Sisa Utang": 0,
                        }
                        df_baru = pd.concat([df_baru, pd.DataFrame([catatan_pelunasan])], ignore_index=True)
                        simpan_excel(df_baru, FILE_EXCEL)

                        if sisa_bayar != 0:
                            st.warning("Ada sisa nominal yang tidak terpakai. Silakan cek ulang data.")
                        else:
                            st.success("Pembayaran utang berhasil disimpan.")
                            st.rerun()


with tab3:
    st.subheader("Daftarkan Produk Baru atau Tambah Stok")
    st.write("Isi nama barang, harga jual, dan stok masuk. Jika produk sudah ada, stok akan ditambah dan harga diperbarui.")

    with st.form("form_barang", clear_on_submit=True):
        nama_barang_baru = st.text_input("Nama barang / produk", placeholder="Contoh: Minyak Goreng 1L")
        harga_jual_baru = st.number_input("Harga jual satuan", min_value=0, step=500)
        jumlah_stok_baru = st.number_input("Jumlah stok masuk", min_value=1, step=1)
        submit_barang = st.form_submit_button("Simpan ke Gudang", type="primary")

        if submit_barang:
            if not nama_barang_baru.strip():
                st.error("Nama barang tidak boleh kosong.")
            else:
                df_gudang = muat_stok()
                nama_bersih = nama_barang_baru.strip()
                mask = df_gudang["Nama Barang"].astype(str).str.lower() == nama_bersih.lower()

                if mask.any():
                    nama_asli = str(df_gudang.loc[mask, "Nama Barang"].iloc[0])
                    df_gudang.loc[mask, "Stok"] = (
                        pd.to_numeric(df_gudang.loc[mask, "Stok"], errors="coerce").fillna(0).astype(int)
                        + int(jumlah_stok_baru)
                    )
                    df_gudang.loc[mask, "Harga Satuan"] = int(harga_jual_baru)
                    simpan_excel(df_gudang, FILE_STOK)
                    st.success(
                        f"Produk `{nama_asli}` diperbarui. "
                        f"Stok bertambah {int(jumlah_stok_baru)} dan harga menjadi {rupiah(harga_jual_baru)}."
                    )
                else:
                    data_baru = pd.DataFrame(
                        [
                            {
                                "Nama Barang": nama_bersih,
                                "Harga Satuan": int(harga_jual_baru),
                                "Stok": int(jumlah_stok_baru),
                            }
                        ]
                    )
                    df_gudang = pd.concat([df_gudang, data_baru], ignore_index=True)
                    simpan_excel(df_gudang, FILE_STOK)
                    st.success(f"Produk baru `{nama_bersih}` berhasil ditambahkan ke gudang.")
                st.rerun()


with tab4:
    st.subheader("Stok Gudang dan Manajemen Produk")
    df_tampil = muat_stok()
    if df_tampil.empty:
        st.info("Gudang produk masih kosong.")
    else:
        keyword = st.text_input("Cari produk", placeholder="Ketik nama barang...")
        df_filter = df_tampil.copy()
        if keyword.strip():
            df_filter = df_filter[
                df_filter["Nama Barang"].str.contains(keyword.strip(), case=False, na=False)
            ]

        st.dataframe(
            df_filter,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Harga Satuan": st.column_config.NumberColumn(format="Rp %d"),
            },
        )

        st.write("---")
        st.markdown("### Hapus Produk")
        st.caption("Gunakan menu ini dengan hati-hati. Produk yang dihapus akan hilang dari gudang.")

        with st.form("form_hapus_produk"):
            nama_hapus = st.selectbox("Pilih produk yang ingin dihapus", df_tampil["Nama Barang"].tolist())
            konfirmasi = st.checkbox("Saya yakin ingin menghapus produk ini secara permanen.")
            submit_hapus = st.form_submit_button("Hapus Produk", type="primary")

            if submit_hapus:
                if not konfirmasi:
                    st.error("Centang konfirmasi terlebih dahulu sebelum menghapus produk.")
                else:
                    df_baru = df_tampil[df_tampil["Nama Barang"] != nama_hapus].reset_index(drop=True)
                    simpan_excel(df_baru, FILE_STOK)
                    st.success(f"Produk `{nama_hapus}` berhasil dihapus dari gudang.")
                    st.rerun()

        st.write("---")
        st.download_button(
            label="Unduh Data Stok Excel",
            data=FILE_STOK.read_bytes(),
            file_name=FILE_STOK.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


with tab5:
    st.subheader("Pengaturan Toko")
    with st.form("form_pengaturan"):
        nama_toko_baru = st.text_input("Nama toko", value=nama_toko)
        submit_nama = st.form_submit_button("Simpan Perubahan", type="primary")
        if submit_nama:
            if not nama_toko_baru.strip():
                st.error("Nama toko tidak boleh kosong.")
            else:
                simpan_nama_toko(nama_toko_baru)
                st.success("Nama toko berhasil diperbarui.")
                st.rerun()

    st.write("---")
    st.markdown("### Backup Data")
    col_download_1, col_download_2 = st.columns(2)
    with col_download_1:
        st.download_button(
            label="Unduh Laporan Keuangan",
            data=FILE_EXCEL.read_bytes(),
            file_name=FILE_EXCEL.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with col_download_2:
        st.download_button(
            label="Unduh Data Stok",
            data=FILE_STOK.read_bytes(),
            file_name=FILE_STOK.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )