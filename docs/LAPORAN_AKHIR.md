# Laporan Akhir

## 1. Hasil evaluasi

Tempel keluaran `python evaluate.py` setelah `data/ground_truth.csv` dilengkapi.

py evaluate.py

Dievaluasi: audit.sql, campuran_error.sql, laporan_penjualan.sql, pemeliharaan.sql (27 triple)

Metode   Precision  Recall     F1
parser        1.00    1.00   1.00
regex         0.65    0.81   0.72

[regex]
  salah ditemukan (FP): ('audit.sql', 16, 'sesi', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 4, 'pesanan', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 8, 'keranjang', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'D')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pesanan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'rahasia', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 15, 'pesanan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.alamat', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.pelanggan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'pelanggan_lama', 'U')
  salah ditemukan (FP): ('pemeliharaan.sql', 15, 'crm.alamat', 'R')
  terlewat (FN):       ('audit.sql', 2, 'pesanan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pelanggan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pesanan', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.alamat', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.pelanggan', 'R')

## 2. Tiga kasus di mana regex salah

Untuk tiap kasus: SQL-nya, kesalahan regex, dan mengapa parser benar (kaitkan dengan konsep
lexing, parsing, atau resolusi).

1.SQL di dalam komentar atau string dianggap statement
    Kesalahan regex: melaporkan pelanggan D, padahal itu komentar. Ini kemungkinan sumber FP ('laporan_penjualan.sql', 2, 'pelanggan', 'D') dan rahasia R.

2.Subquery di UPDATE/DELETE diberi operasi statement 
    Mengapa parser benar: lexer (Crafting Interpreters bab 4) membuang komentar sebelum token terbentuk dan memperlakukan isi '...' sebagai satu token STRING. Parser tidak pernah melihat teks itu. Regex bekerja pada teks datar tanpa konsep token.

3.Nomor baris salah dan statement rusak ikut dihitung
    UPDATE pelanggan_lama SET x = (SELECT y FROM crm.alamat);
    Kesalahan regex: tidak membedakan tabel target dan tabel yang hanya dibaca lewat subquery, sehingga operasinya bisa tertukar atau ganda (kemungkinan FP crm.alamat R dan pelanggan_lama U di pemeliharaan.sql).

    Mengapa parser benar: grammar punya struktur bersarang. Parser mengenali (SELECT ...) sebagai node Subquery di dalam Update, dan analyzer menerapkan aturan “subquery selalu R” pada AST. Regex tidak bisa merepresentasikan nesting.

## 3. Batas pendekatan kami

Minimal tiga hal yang **tidak bisa** ditangani dengan benar oleh tool ini meskipun semua bug
sudah diperbaiki. Untuk tiap batas: contoh SQL atau situasinya, akibatnya pada CRUD matrix,
dan informasi apa yang dibutuhkan untuk mengatasinya.

1.Tidak ada skema database
    Contoh SQL / Situasi: SELECT status FROM pesanan, pengiriman; (kolom status tidak memiliki awalan alias tabel, dan program menemukan lebih dari 1 tabel di scope yang sama).

    Akibat pada CRUD Matrix: Ini adalah kelemahan yang baru saja Anda amankan di TODO 2. Meskipun table name berhasil ditangkap sebagai R oleh Parser, Resolver gagal menautkan kolom status ke tabel pemantiknya (menghasilkan status warning / ambigu). Jika sistem matriks ini diperluas untuk melacak operasi CRUD di tingkat kolom (bukan hanya tingkat tabel), datanya akan cacat atau tidak akurat.

    nformasi untuk Mengatasinya: Program membutuhkan akses ke skema struktur tabel asli untuk melakukan pencocokan nama kolom (melihat apakah status adalah milik tabel pesanan atau pengiriman).

2.Ambiguitas Mutlak Kolom Tanpa Qualifier pada Multiple Tables
   Contoh SQL / Situasi: SELECT status FROM pesanan, pengiriman; (kolom status tidak memiliki awalan alias tabel, dan program menemukan lebih dari 1 tabel di scope yang sama).

   Akibat pada CRUD Matrix: Ini adalah kelemahan yang baru saja Anda amankan di TODO 2. Meskipun table name berhasil ditangkap sebagai R oleh Parser, Resolver gagal menautkan kolom status ke tabel pemantiknya (menghasilkan status warning / ambigu). Jika sistem matriks ini diperluas untuk melacak operasi CRUD di tingkat kolom (bukan hanya tingkat tabel), datanya akan cacat atau tidak akurat.

   Informasi untuk Mengatasinya: Program membutuhkan akses ke skema struktur tabel asli untuk melakukan pencocokan nama kolom (melihat apakah status adalah milik tabel pesanan atau pengiriman).

3.Keterbatasan Tata Bahasa untuk Tabel Sementara / CTE (Common Table Expressions)
    Contoh SQL / Situasi: WITH data_sementara AS (SELECT id FROM pelanggan) SELECT * FROM data_sementara;

    Akibat pada CRUD Matrix: Karena tata bahasa kita (subset SQL) tidak mendukung keyword WITH, Lexer atau Parser akan langsung melempar pesan error saat menemukan awalan sintaks ini. Sekalipun kata WITH ditambahkan secara paksa, Resolver akan mencatat data_sementara sebagai operasi R di matriks akhir, padahal itu hanyalah tabel virtual yang hanya ada di memori saat query berjalan (bukan tabel fisik).

    Informasi untuk Mengatasinya: Membutuhkan perluasan grammar EBNF di modul Parser untuk menangani blok CTE, dan pembaruan pada modul Resolver untuk mendaftarkan tabel CTE ke dalam scope terpisah (ruang lingkup virtual). Hal ini agar analyzer mengabaikan nama-nama tabel sementara tersebut saat menyusun laporan matriks akhir.
    
## 4. Pembagian kerja

Septian mengerjakan TODO(T3) beserta bug-bug di `lexer.py`, lalu menulis test
regresi dan test kasus tepinya di `tests/test_tambahan.py`.

Khalifah mengerjakan TODO(T1) dan TODO(T2) beserta bug-bugnya, lalu menulis test
tambahannya di `tests/test_tambahan.py`.

**Cara kami memastikan keduanya memahami seluruh kode:**
- kami berdua mengerjakan TODO-TODO lalu mencoba menyelesaikan bug-bugnya di branch masing-masing agar paham, lalu berdiskusi kode siapa yang akan dimasukkan ke dalam main
- Kedua anggota memiliki commit di repositori Git.
