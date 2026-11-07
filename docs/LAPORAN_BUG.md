# Laporan Bug

Bug di bagian parser (`crud/parser.py`) dan resolver (`crud/resolver.py`). Rujukan "§" adalah bagian di
SPESIFIKASI.md. Rujukan "bab" adalah bab di *Crafting Interpreters*.

---

## Bug 1: `AND` dan `OR` diperlakukan setara

**Ditemukan oleh:** [Khalifah] · **Diperbaiki oleh:** [Khalifah]

**Gejala.** `a = 1 OR b = 2 AND c = 3` diparse sebagai `(a = 1 OR b = 2) AND c = 3`. Akar pohon
`WHERE` bernilai `AND`, padahal menurut §3.1 `AND` lebih kuat daripada `OR` sehingga akarnya harus `OR`
dengan `AND(b = 2, c = 3)` di cabang kanan. Tabel CRUD tidak berubah, jadi bug ini tidak terlihat dari
matrix, tetapi bentuk AST (API publik `ast_nodes`) salah.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT a FROM t WHERE a = 1 OR b = 2 AND c = 3;
```

Hasil di kode lama: akar `BinaryOp 'AND'`, cabang kiri `OR`. Hasil yang diharapkan: akar `OR`, cabang
kanan `AND`.

**Akar masalah.** Fungsi `_logical` memakai satu loop `while self._check_kw("AND", "OR")`, sehingga
kedua operator berada pada tingkat presedensi yang sama dan digabung dari kiri ke kanan. Pada recursive
descent (bab 6, *Parsing Expressions*), presedensi tidak disimpan di tabel tersendiri, tetapi muncul dari
struktur pemanggilan: operator yang lebih lemah berada di fungsi yang lebih atas dan memanggil fungsi
operator yang lebih kuat. Kode lama menghilangkan satu tingkat itu, yaitu tingkat `AND`, sehingga
tabel §3.1 tidak terpenuhi.

**Perbaikan.** `_logical` sekarang hanya mengurus `OR` dan memanggil fungsi baru `_and` untuk
operand-nya. `_and` mengurus `AND` dan memanggil `_not`. Urutan pemanggilannya sama dengan tabel
presedensi di §3.1. Alternatif yang dipertimbangkan adalah precedence climbing dengan tabel prioritas
operator. Itu tidak dipilih karena menambah mekanisme baru, padahal grammar §3 sudah berbentuk
bertingkat dan satu fungsi per tingkat lebih mudah dicocokkan dengan spek.

**Test regresi.** `test_and_lebih_kuat_dari_or` (gagal sebelum perbaikan, lulus sesudahnya).

**Peran AI.** [isi dengan jujur] AI membantu menemukan bug ini lewat membaca kode dan menjalankan
parser pada contoh `a = 1 OR b = 2 AND c = 3`, lalu menulis perbaikannya. Verifikasi: test regresi
dijalankan pada kode lama (gagal) dan kode baru (lulus), dan bentuk pohon dicek dengan `pretty()`.

---

## Bug 2: Error recovery membuang sisa file

**Ditemukan oleh:** [Khalifah] · **Diperbaiki oleh:** [Khalifah]

**Gejala.** Setelah satu statement rusak, semua statement valid sesudahnya hilang dari hasil. Menurut §6,
recovery harus membuang token sampai dan termasuk `;` berikutnya, lalu statement sesudahnya tetap
diproses. Satu statement rusak menghasilkan tepat satu error.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT FROM a; DELETE FROM d;
```

Hasil di kode lama: satu error dan matrix kosong. Hasil yang diharapkan: satu error dan `d: D`.

**Akar masalah.** `_synchronize` berupa loop `while not self._at_end(): self._advance()`, yaitu membuang
token sampai akhir input dan tidak pernah berhenti di `;`. Pada panic mode (bab 6, bagian *Panic Mode
Error Recovery*), fungsi sinkronisasi harus mengenali titik aman, yaitu batas statement, dan berhenti di
sana supaya parser bisa melanjutkan. Tanpa titik berhenti, mode panic berubah menjadi "hentikan seluruh
file".

**Perbaikan.** `_synchronize` sekarang membuang token sambil memeriksa tipe tiap token yang dikonsumsi,
lalu `return` setelah mengonsumsi `SEMICOLON`. Alternatif: berhenti di keyword awal statement (`SELECT`,
`INSERT`, dan seterusnya). Itu tidak dipilih karena `SELECT` juga muncul di dalam subquery, sehingga
recovery bisa berhenti di tengah statement rusak dan menghasilkan lebih dari satu error untuk satu
statement, bertentangan dengan §6. Titik koma di dalam string tidak mengganggu karena lexer sudah
mengubah isi string menjadi satu token `STRING`.

**Test regresi.** `test_recovery_berhenti_di_titik_koma` (gagal sebelum perbaikan, lulus sesudahnya).

**Peran AI.** [isi dengan jujur] AI menemukan bug ini ketika membaca `_synchronize` dan mencocokkannya
dengan §6, lalu menguji lewat kasus `SELECT FROM a; ...`. Verifikasi: test regresi, serta kasus string
berisi `;` yang dijalankan sendiri.

---

## Bug 3: `LEFT OUTER JOIN` ditolak

**Ditemukan oleh:** [Khalifah] · **Diperbaiki oleh:** [Khalifah]

**Gejala.** Query dengan `LEFT OUTER JOIN` gagal dengan `Baris 1, kolom 25: diharapkan JOIN, ditemukan
'OUTER'` dan statement tidak masuk matrix. Grammar §3 mengizinkan `"LEFT" [ "OUTER" ]` sebelum `JOIN`.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT a.id FROM a LEFT OUTER JOIN b ON b.k = a.id;
```

Hasil di kode lama: satu error dan matrix kosong. Hasil yang diharapkan: `a: R`, `b: R`, tanpa error.

**Akar masalah.** Fungsi `_join` meniru grammar dengan benar untuk `INNER` dan `LEFT`, tetapi lupa
bagian opsional `[ "OUTER" ]`. Pada recursive descent (bab 6), setiap unsur opsional di grammar harus
dipetakan ke satu pemeriksaan opsional di fungsi yang bersangkutan. Unsur yang tidak diperiksa membuat
parser menolak input yang sebenarnya sah.

**Perbaikan.** Di `_join`, setelah `LEFT` ditambahkan `self._match_kw("OUTER")`. Nilai `kind` tetap
`"LEFT"`. Alternatif: membuat nilai `kind` baru `"LEFT OUTER"`. Itu tidak dipilih karena mengubah isi
field di AST (API publik) padahal maknanya sama dengan `LEFT JOIN`.

**Test regresi.** `test_left_outer_join` (gagal sebelum perbaikan, lulus sesudahnya).

**Peran AI.** [isi dengan jujur] AI menemukan bug ini lewat membandingkan `_join` dengan grammar §3,
lalu menjalankan query yang memuat `LEFT OUTER JOIN`. Verifikasi: test regresi dan membaca
`pemeliharaan.sql` baris 5.

---

## Bug 4: Pencarian alias berqualifier dimulai dari scope terluar

**Ditemukan oleh:** [Khalifah] · **Diperbaiki oleh:** [Khalifah]

**Gejala.** Alias yang sama di subquery dan di luarnya (shadowing) di-resolve ke tabel luar. Menurut §4.3,
qualifier dicari dari scope terdalam ke luar, sehingga alias di subquery menutupi alias luar. Tidak ada
diagnostik, hasilnya diam-diam salah.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT x.id FROM a x WHERE x.id IN (SELECT x.k FROM b x);
```

Hasil di kode lama: `x.k` ter-resolve ke `a`. Hasil yang diharapkan: `x.k` ke `b`, sedangkan `x.id` di
`SELECT` dan `WHERE` luar tetap ke `a`. Tabel CRUD tidak berubah, tetapi `--kolom` memetakan kolom ke
tabel yang salah.

**Akar masalah.** `_lookup` membangun daftar scope dari scope aktif naik ke induknya, sehingga urutannya
terdalam ke terluar, lalu menelusurinya dengan `reversed(chain)`. Pembalikan itu membuat pencarian
dimulai dari scope terluar. Pada resolver (bab 11, *Resolving and Binding*), variabel dicari dari scope
paling dalam ke arah luar dan pencarian berhenti di temuan pertama. Itulah yang membuat deklarasi lokal
menutupi deklarasi di scope yang lebih luar. Urutan terbalik merusak aturan itu.

**Perbaikan.** `reversed(chain)` diganti `chain`, sehingga loop dimulai dari scope terdalam. Alternatif:
satu kamus datar alias ke tabel untuk seluruh statement. Itu tidak dipilih karena tidak bisa membedakan
alias yang sama di scope yang berbeda (contoh di `audit.sql` baris 14).

**Test regresi.** `test_shadowing_alias_terdalam_menang` (gagal sebelum perbaikan, lulus sesudahnya).

**Peran AI.** [isi dengan jujur] AI menemukan bug ini lewat membaca `_lookup` dan mencocokkannya dengan
§4.3, lalu menjalankan contoh shadowing. Verifikasi: test regresi dan membandingkan `resolved` tiap
`ColumnRef` sebelum dan sesudah perbaikan.

---

## Bug 5: Scope `DELETE` tidak ditutup

**Ditemukan oleh:** [Khalifah] · **Diperbaiki oleh:** [Khalifah]

**Gejala.** Alias dari statement `DELETE` terlihat oleh statement berikutnya. Menurut §4.5, setelah satu
statement selesai di-resolve, tidak boleh ada scope tersisa. Error yang seharusnya muncul justru tidak
dilaporkan.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
DELETE FROM a s WHERE s.x = 1; SELECT s.id FROM b u;
```

Hasil di kode lama: tidak ada diagnostik. Hasil yang diharapkan: error `alias 's' tidak terdefinisi`
pada `SELECT`, karena `s` hanya milik statement `DELETE`.

**Akar masalah.** `_delete` memanggil `_push()` untuk membuat scope, tetapi tidak pernah memanggil
`_pop()`. Resolver menyimpan scope sebagai tumpukan (bab 11): setiap `beginScope` harus berpasangan
dengan `endScope`, kalau tidak, scope yang bocor menjadi induk bagi semua scope berikutnya. Itulah
mengapa alias `s` dari statement pertama masih ditemukan oleh statement kedua.

**Perbaikan.** Menambahkan `self._pop()` di akhir `_delete`, sehingga `_push` dan `_pop` berpasangan
seperti di `_select` dan `_update`. Alternatif: mengosongkan `self.scope` di awal tiap statement di
`resolve_script`. Itu tidak dipilih karena hanya menutupi gejala dan membiarkan ketidakseimbangan push/pop
di fungsi lain tetap tersembunyi.

**Test regresi.** `test_alias_delete_tidak_bocor_ke_statement_berikutnya` (gagal sebelum perbaikan, lulus
sesudahnya).

**Peran AI.** [isi dengan jujur] AI menemukan bug ini lewat membaca ketiga fungsi `_select`, `_update`,
dan `_delete` secara berdampingan, lalu menjalankan contoh di atas. Verifikasi: test regresi dan kasus
`audit.sql` baris 16 dan 18.

-- Bug 6-9 DItemukan oleh: Septian Fakhrul Hikam

## Bug 6:_synchronize membuang semua token sampai EOF
    Akar masalah: _synchronize membuang token sampai EOF dan tidak pernah berhenti di batas statement. Pada panic mode (bab 6), parser membuang token sampai titik sinkronisasi lalu melanjutkan parsing. Di SQL titik amannya adalah ;, dan spesifikasi 6 meminta pembuangan sampai; dan termasuk berikutnya. Tanpa titik berhenti, satu error membuat seluruh sisa file hilang dari hasil.

    Gimana solusinya?
    Konsumsi token satu per satu dan return tepat setelah token SEMICOLON ikut dikonsumsi. Karena ; di dalam string sudah menjadi satu token STRING dari lexer, ia tidak memicu berhenti palsu.

## Bug 7: Keyword huruf kecil dianggap IDENT
    Akar masalah: Lexer memeriksa apakah teks asli kata ada di KEYWORDS, padahal isi KEYWORDS hanya huruf besar. Akibatnya select, From, atau Where gagal cocok dan menjadi IDENT, bukan KEYWORD. Spesifikasi 2.2 meminta keyword tidak peka huruf besar/kecil dan nilai tokennya dinormalisasi ke huruf besar. Pembandingan harus memakai bentuk yang sudah dinormalisasi. Kata yang hanya diawali keyword (selection) tetap IDENT karena seluruh kata dibaca dulu baru dicek ke tabel keyword (bab 4: identifier vs reserved word).

    Gimana solusinya?

    Normalisasi dulu dengan text_upper = text.upper(), cek text_upper in KEYWORDS, lalu simpan text_upper sebagai nilai token KEYWORD. Token IDENT tetap memakai teks asli
## Bug 8: Bug Kutip Tunggal di Dalam String
    Akar masalah: saat program bertemu dengan satu tanda kutip ('), program akan langsung melakukan break (berhenti membaca string). Padahal, spesifikasi meminta agar dua tanda kutip yang berurutan ('') di dalam string (seperti pada kata 'O''Brien') dianggap sebagai satu karakter kutip biasa, bukan penutup string

    Gimana solusinya?
    Harus dicek juga apakah karakter selanjutnya adalah kutip tunggal juga

## Bug 9: Operator Tidak Lengkap (<>)
    Akar masalah: Spesifikasi bagian 2.5 menyatakan bahwa <> adalah salah satu operator valid dan sistem harus membaca operator terpanjang yang cocok (maximal munch). Pada kode awal yang kamu berikan, saat bertemu karakter <, program hanya mengecek apakah karakter selanjutnya adalah = (untuk menjadi <=). Jika diberikan <>, lexer akan gagal membacanya sebagai satu kesatuan

    gimana solusinya?

    Setelah < periksa karakter berikutnya secara berurutan: = menghasilkan <=, > menghasilkan <>, selain itu <. Lexer selalu mengambil operator terpanjang yang cocok (maximal munch, bab 4), jadi <> menjadi satu token OP, bukan < lalu >.
