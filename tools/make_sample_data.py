"""Generate the fictional sample documents used in the labs.

Run from the repo root (lecturer only, needs: pip install reportlab pillow):
    python tools/make_sample_data.py
Creates data/*.pdf, data/archive/*.pdf and data/sample_requests/*.jpg.
All content is FICTIONAL lab material, not official UIB regulation.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
NOTICE = "CONTOH FIKTIF UNTUK PRAKTIKUM — bukan peraturan resmi UIB"

HANDBOOK_2026 = [
    ("Kata Pengantar", [
        "Buku Panduan Mahasiswa 2026 ini berisi informasi akademik dan layanan kampus yang perlu diketahui "
        "setiap mahasiswa. Bacalah buku ini bersama Peraturan Akademik 2026.",
        "Jika terdapat perbedaan antara buku panduan ini dan Peraturan Akademik, maka yang berlaku adalah "
        "Peraturan Akademik."]),
    ("Visi dan Misi", [
        "Visi universitas adalah menjadi universitas internasional yang unggul dalam teknologi dan "
        "kewirausahaan.",
        "Misi universitas adalah menyelenggarakan pendidikan yang relevan dengan industri, melakukan penelitian "
        "terapan, dan melayani masyarakat."]),
    ("Sistem Semester", [
        "Satu tahun akademik terdiri dari semester ganjil dan semester genap. Setiap semester terdiri dari 16 "
        "minggu, termasuk satu minggu Ujian Tengah Semester (UTS) dan satu minggu Ujian Akhir Semester (UAS).",
        "Setiap mata kuliah dilaksanakan dalam 14 pertemuan tatap muka ditambah UTS dan UAS.",
        "Tanggal penting setiap semester diumumkan dalam kalender akademik di portal mahasiswa."]),
    ("Registrasi dan KRS", [
        "Mahasiswa wajib melakukan registrasi dan mengisi Kartu Rencana Studi (KRS) secara online melalui portal "
        "akademik pada masa KRS yang tercantum dalam kalender akademik.",
        "KRS harus disetujui oleh dosen wali sebelum batas akhir masa KRS. Mahasiswa yang tidak mengisi KRS "
        "dianggap tidak aktif pada semester tersebut."]),
    ("Dosen Wali", [
        "Setiap mahasiswa memiliki satu dosen wali yang membimbing perencanaan studi.",
        "Mahasiswa wajib berkonsultasi dengan dosen wali sebelum mengisi KRS, terutama jika ingin mengambil "
        "beban studi lebih dari 20 SKS."]),
    ("Sistem Kredit Semester", [
        "Beban studi dinyatakan dalam Satuan Kredit Semester (SKS). Satu SKS kuliah setara dengan 50 menit tatap "
        "muka, 60 menit tugas terstruktur, dan 60 menit belajar mandiri per minggu.",
        "Ketentuan beban SKS maksimal per semester diatur dalam Peraturan Akademik 2026."]),
    ("Sistem Penilaian", [
        "Nilai akhir mata kuliah dinyatakan dalam huruf dengan bobot sebagai berikut: A = 4,0; A- = 3,7; "
        "B+ = 3,3; B = 3,0; B- = 2,7; C+ = 2,3; C = 2,0; D = 1,0; E = 0.",
        "Nilai D dan E pada mata kuliah wajib harus diperbaiki dengan mengulang mata kuliah tersebut."]),
    ("IPS dan IPK", [
        "Indeks Prestasi Semester (IPS) dihitung dari nilai seluruh mata kuliah pada satu semester. Indeks "
        "Prestasi Kumulatif (IPK) dihitung dari seluruh mata kuliah yang telah ditempuh.",
        "Rumus: jumlah (bobot nilai x SKS) dibagi jumlah SKS. Contoh: A (3 SKS), B+ (3 SKS), A- (2 SKS) "
        "menghasilkan (12 + 9,9 + 7,4) / 8 = 3,66."]),
    ("Layanan BAAK", [
        "Biro Administrasi Akademik dan Kemahasiswaan (BAAK) melayani surat keterangan aktif kuliah, transkrip "
        "sementara, dan permohonan cuti akademik.",
        "Surat keterangan aktif kuliah diajukan melalui formulir layanan dengan melampirkan foto Kartu Tanda "
        "Mahasiswa (KTM). Surat diproses paling lama 2 hari kerja.",
        "Keluhan terkait fasilitas atau layanan dapat disampaikan melalui formulir yang sama."]),
    ("Beasiswa", [
        "Universitas menyediakan beasiswa prestasi akademik bagi mahasiswa dengan IPK minimal 3,50 dan beasiswa "
        "bantuan biaya pendidikan.",
        "Pendaftaran beasiswa memerlukan surat keterangan aktif kuliah dan transkrip nilai terbaru."]),
    ("Fasilitas Kampus", [
        "Perpustakaan buka Senin sampai Jumat pukul 08.00 sampai 20.00 dan Sabtu pukul 08.00 sampai 14.00.",
        "Laboratorium komputer dapat dipakai di luar jam kuliah dengan menunjukkan KTM."]),
    ("Kehadiran Perkuliahan", [
        "Mahasiswa wajib hadir minimal 75% dari seluruh pertemuan tatap muka pada setiap mata kuliah.",
        "Untuk mata kuliah dengan 14 pertemuan, mahasiswa boleh tidak hadir paling banyak 3 kali.",
        "Mahasiswa yang kehadirannya kurang dari 75% tidak diperkenankan mengikuti UAS mata kuliah tersebut. "
        "Ketentuan izin sakit diatur dalam Peraturan Akademik 2026."]),
    ("Etika Akademik", [
        "Plagiarisme, menyontek, dan pemalsuan dokumen merupakan pelanggaran berat.",
        "Penggunaan alat bantu kecerdasan buatan dalam tugas wajib mengikuti ketentuan dosen pengampu dan "
        "dicantumkan secara jujur."]),
    ("Kontak Layanan", [
        "BAAK melayani mahasiswa Senin sampai Jumat pukul 08.00 sampai 16.00.",
        "Pertanyaan yang tidak terjawab dalam buku panduan ini dapat diajukan langsung ke BAAK atau dosen wali."]),
]


def rules(year):
    sks = ("Beban studi normal adalah maksimal 20 SKS per semester. Mahasiswa dengan IPK di atas atau sama "
           "dengan 3,50 boleh mengambil hingga 24 SKS. Mahasiswa dengan IPK di bawah 2,00 maksimal 15 SKS."
           if year == 2026 else
           "Beban studi normal adalah maksimal 22 SKS per semester. Mahasiswa dengan IPK di atas atau sama "
           "dengan 3,00 boleh mengambil hingga 24 SKS.")
    graduate = ["Mahasiswa dinyatakan lulus jika telah menempuh minimal 144 SKS, IPK minimal 2,00, dan tidak "
                "memiliki nilai E."]
    if year == 2026:
        graduate.append("Mulai tahun 2026, mahasiswa juga wajib memiliki sertifikat kemampuan bahasa Inggris "
                        "dengan skor minimal 450.")
    return [
        ("Ketentuan Umum", [
            f"Peraturan Akademik {year} mengatur penyelenggaraan pendidikan bagi seluruh mahasiswa program "
            "sarjana.",
            "Peraturan ini berlaku sejak semester ganjil tahun berjalan."]),
        ("Status Mahasiswa", [
            "Status mahasiswa terdiri dari aktif, cuti akademik, dan non-aktif.",
            "Mahasiswa aktif adalah mahasiswa yang telah melakukan registrasi dan mengisi KRS."]),
        ("Pendaftaran Ulang", [
            "Pendaftaran ulang dilakukan setiap semester dengan melunasi biaya pendidikan sebelum masa KRS "
            "berakhir.",
            "Keterlambatan pembayaran dikenakan denda sesuai ketentuan keuangan."]),
        ("Izin Tidak Hadir", [
            "Izin sakit wajib melampirkan surat keterangan dokter yang diserahkan paling lambat 3 hari kerja "
            "setelah tidak hadir.",
            "Izin yang sah dicatat oleh dosen, namun tetap dihitung dalam batas kehadiran minimal 75%."]),
        ("Cuti Akademik", [
            "Cuti akademik dapat diajukan oleh mahasiswa yang telah menempuh minimal 2 semester dan tidak "
            "memiliki tunggakan biaya.",
            "Permohonan cuti diajukan paling lambat 2 minggu sebelum perkuliahan dimulai, sesuai batas cuti "
            "pada kalender akademik.",
            "Cuti akademik paling lama 2 semester selama masa studi."]),
        ("Ujian", [
            "Mahasiswa dapat mengikuti UAS jika kehadirannya minimal 75%.",
            "Ujian susulan hanya diberikan untuk alasan sakit dengan surat dokter atau tugas resmi universitas."]),
        ("Beban Studi", [sks, "Mahasiswa semester 1 dan 2 mengambil paket mata kuliah yang ditetapkan program "
                              "studi."]),
        ("Biaya Akademik", [
            "Biaya cuti akademik adalah Rp 1.500.000 per semester.",
            "Biaya wisuda adalah Rp 2.000.000 dan dibayarkan saat pendaftaran wisuda."]),
        ("Kelulusan", graduate),
        ("Predikat Kelulusan", [
            "Predikat dengan pujian (cum laude) diberikan kepada lulusan dengan IPK minimal 3,51 dan masa studi "
            "paling lama 4 tahun.",
            "Predikat sangat memuaskan diberikan kepada lulusan dengan IPK 3,01 sampai 3,50."]),
    ]


def make_pdf(path, title, pages):
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica-Oblique", 8)
        canvas.drawString(56, 30, f"{NOTICE}  ·  {title}  ·  halaman {doc.page}")
        canvas.restoreState()

    story = []
    for i, (heading, paras) in enumerate(pages):
        story.append(Paragraph(f"{title}", styles["Normal"]))
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"{i + 1}. {heading}", styles["Heading2"]))
        for p in paras:
            story.append(Paragraph(p, styles["BodyText"]))
            story.append(Spacer(1, 6))
        if i < len(pages) - 1:
            story.append(PageBreak())
    SimpleDocTemplate(str(path), pagesize=A4, title=title).build(story, onFirstPage=footer, onLaterPages=footer)
    print("wrote", path.relative_to(ROOT))


def make_card(path, lines, blur=0):
    img = Image.new("RGB", (900, 560), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("Arial.ttf", 30)
        big = ImageFont.truetype("Arial.ttf", 38)
    except OSError:
        font = big = ImageFont.load_default()
    d.rectangle([10, 10, 890, 550], outline="black", width=4)
    d.text((40, 30), lines[0], fill="black", font=big)
    for i, line in enumerate(lines[1:]):
        d.text((40, 110 + i * 60), line, fill="black", font=font)
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, quality=90)
    print("wrote", path.relative_to(ROOT))


if __name__ == "__main__":
    make_pdf(DATA / "student_handbook_2026.pdf", "Buku Panduan Mahasiswa 2026", HANDBOOK_2026)
    make_pdf(DATA / "academic_rules.pdf", "Peraturan Akademik 2026", rules(2026))
    make_pdf(DATA / "archive" / "academic_rules_2024.pdf", "Peraturan Akademik 2024", rules(2024))
    req = DATA / "sample_requests"
    make_card(req / "ktm_active_letter.jpg", ["KARTU MAHASISWA (CONTOH)", "Nama: Siti Rahma", "NIM: 2231001",
                                              "Prodi: Informatika",
                                              "Permohonan: surat aktif kuliah untuk beasiswa"])
    make_card(req / "leave_request.jpg", ["FORMULIR PERMOHONAN (CONTOH)", "Nama: Budi Santoso", "NIM: 2231002",
                                          "Prodi: Sistem Informasi",
                                          "Permohonan: cuti akademik semester depan"])
    make_card(req / "blurry_card.jpg", ["KARTU MAHASISWA (CONTOH)", "Nama: Andi Wijaya", "NIM: 2231003",
                                        "Prodi: Informatika", "Permohonan: surat aktif kuliah"], blur=9)
