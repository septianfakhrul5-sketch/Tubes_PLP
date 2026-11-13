# Kartu Desain

Tuliskan lima keputusan desain penting dalam pekerjaan kalian. Untuk tiap keputusan, sebutkan
alternatif yang ditolak dan alasannya. Contoh topik (boleh memilih yang lain):

- bagaimana parser membedakan `*` sebagai "semua kolom" dan sebagai perkalian;
- di mana dan bagaimana presedensi `AND`/`OR` dinyatakan;
- mengapa error recovery berhenti di `;`, bukan di keyword `SELECT` berikutnya;
- urutan pencarian scope dan akibatnya pada shadowing serta correlated subquery;
- mengapa kolom tanpa qualifier hanya dilihat di scope terdalam, dan apa kelemahannya;
- bagaimana implementasi `INSERT ... SELECT` atau komentar blok kalian.

| No | Keputusan | Alternatif yang ditolak | Alasan |
| --- | --- | --- | --- |
| 1 | Parser menangani `INSERT ... SELECT` dengan memanggil `self._select()` lalu menyimpannya dalam `ast.Insert` dengan nilai `values` diatur menjadi `None`. | Membuat dua representasi node AST yang sepenuhnya berbeda (misalnya `ast.InsertValues` dan `ast.InsertSelect`). | Menggunakan satu node `ast.Insert` yang sama mempertahankan struktur yang lebih sederhana bagi Analyzer di hilir. Analyzer dapat langsung mencatat target `INSERT` sebagai Create (C) dan secara rekursif memproses klausa `SELECT` di dalamnya sebagai Read (R). |

| 2 | Implementasi komentar blok (`/* ... */`) di Lexer dilakukan dengan *looping* yang mengkonsumsi karakter hingga menemukan `*/`, tanpa menghasilkan objek token. | Membuat token khusus (misal `TokenType.COMMENT`) lalu meneruskannya ke Parser, atau mengekstraknya menggunakan Regex. | Tidak membuat token meringankan kerja Parser, karena Parser tidak perlu dirancang untuk mengabaikan sisipan komentar di setiap sela sintaks SQL. Pemindaian manual (tanpa Regex) juga memastikan Lexer tetap bisa menghitung baris baru (`\n`) di dalam komentar agar pesan *error* tetap akurat.| 

| 3 | **Presedensi `AND`/`OR` dinyatakan lewat hierarki fungsi parser.** `_logical` (OR) memanggil `_and` (AND), `_and` memanggil `_not`, lalu `_comparison`. Setiap fungsi hanya memanggil tingkat di bawahnya, sehingga `a=1 OR b=2 AND c=3` menjadi `OR(a=1, AND(b=2, c=3))`. | (a) Satu loop `while` yang memperlakukan `AND` dan `OR` setara (kode awal). (b) Precedence climbing dengan tabel prioritas operator. | (a) Menghasilkan `AND(OR(...), c=3)`, yang salah menurut tabel §3.1. (b) Menambah mekanisme baru, padahal grammar §3 sudah berbentuk bertingkat. Dengan satu fungsi per tingkat, urutan pemanggilan sama dengan tabel presedensi, jadi mudah dicocokkan baris demi baris dengan spek. |

| 4 | **Error recovery (panic mode) berhenti tepat setelah `;`.** `_synchronize` membuang token sampai dan termasuk `;` berikutnya, lalu parsing statement berikutnya berjalan normal. | (a) Sinkronisasi di keyword awal statement (`SELECT`, `INSERT`, dst.). (b) Membuang token sampai EOF (kode awal). | (a) `SELECT` juga muncul di dalam subquery, sehingga recovery bisa berhenti di tengah statement rusak dan menghasilkan lebih dari satu error (spek §6 meminta tepat satu). (b) Membuat satu error menghapus semua statement valid sesudahnya. Titik koma di dalam string atau komentar aman karena lexer sudah mengubahnya menjadi `STRING` atau membuangnya. Kelemahan: kalau `;` terlewat, statement berikutnya ikut terbuang bersama statement rusak. |

| 5 | **Pencarian alias berqualifier dari scope terdalam ke luar.** `_lookup` menyusun rantai scope dari scope aktif naik lewat `parent`, lalu memakai entri pertama yang ditemukan. | (a) Mencari dari scope terluar (kode awal). (b) Satu kamus datar alias→tabel untuk seluruh statement. | Satu aturan sudah cukup untuk shadowing dan correlated subquery (§4.3): alias dalam menutupi alias luar, dan alias luar tetap terlihat bila tidak ditutupi. Pada (a), `x.k` di subquery terhubung ke tabel luar tanpa diagnostik. Pada (b), `x` di dalam dan di luar subquery (`audit.sql` baris 14) tidak bisa dibedakan. Pencarian berhenti di temuan pertama, jadi tidak ada ambiguitas antarlevel. |

