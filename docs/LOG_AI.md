# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.

| No | Siapa | Prompt / tugas (ringkas) | Hasil: diterima, diubah, atau ditolak | Alasan | Cara verifikasi |
| --- | --- | --- | --- | --- | --- |
| 1 | | Khalifah | Meminta AI untuk menjelaskan pengaruh perbaikan bug terhadap struktur program, perbaikan dilakukan sendiri | Diterima, AI menjelaskan pengaruhnya | Ingin mencari tahu kebenaran atas pengaruh perubahan struktur program jika bug diperbaiki | 

| 2 | | Khalifah | Meminta AI untuk membantu menyusun ground_truth | Diterima, AI membantu langkah penyusunan | Sedikit kesulitan dalam langkah penyusunan ground_truth |

| 3 | | Khalifah | Meminta AI untuk membantu mendiagnosis error saat program di tahap troubleshoot | Diterima, AI membantu tahap troubleshoot dan memberikan penjelasan cara resolve nya | Penasaran akan asal dari error dan membandingkan hasil AI dan hasil temuan sendiri |

| No | Siapa | Prompt / tugas (ringkas) | Hasil: diterima, diubah, atau ditolak | Alasan | Cara verifikasi |
| --- | --- | --- | --- | --- | --- |
| 1 | Septian | Meminta AI membantu mendiagnosis penyebab dua token terpisah (`<` dan `>`) pada operator `<>` di modul Lexer. | Diterima. AI memberikan logika `_match(">")` untuk menggabungkan token. | AI dapat dengan cepat menghubungkan error "diharapkan ekspresi, ditemukan '>'" di Parser dengan kesalahan pemisahan token di Lexer. | Menjalankan `pytest tests/test_tambahan.py` dan melihat `test_operator_tidak_sama_satu_token` menjadi *Passed*. |
| 2 | Septian | Memberikan *traceback* error `TypeError: 'NoneType' object is not iterable` pada tahap Resolver dan Analyzer saat menguji `INSERT ... SELECT`. | Diterima. AI menunjukkan bahwa atribut `values` bernilai `None` dan menyarankan pengecekan `if ins.values is not None:`. | AI memahami struktur AST dari grammar EBNF di spesifikasi, sehingga tahu bahwa node `ast.Insert` pada bentuk `SELECT` tidak akan memiliki klausa `VALUES`. | Menjalankan `pytest` hingga *test case* regresi untuk fungsi tersebut berubah menjadi hijau 100%. |
| 3 | Septian | Meminta AI menyelesaikan logika `TODO(T2)` terkait resolusi kolom tanpa *qualifier* untuk mencari tabel pada *scope* terdalam. | Diubah. AI awalnya menyarankan pemanggilan *list* `self.scopes[-1]` dan `self.scope[-1]`, yang ternyata keliru. | AI tidak memiliki konteks penuh mengenai definisi *class* `Scope` pada awalnya, sehingga memberikan asumsi bentuk *stack* yang salah. | Menjalankan *test*, mendapatkan `AttributeError` dan `TypeError`, lalu memberikan definisi `class Scope` ke AI agar kode diubah menjadi `self.scope.entries`. |

**Refleksi (3-5 kalimat).** 
AI sangat membantu dalam menavigasi tumpukan *error* (traceback) dari `pytest`, terutama dalam menemukan hubungan sebab-akibat lintas modul (misalnya kegagalan di Parser yang ternyata bersumber dari cacat pemotongan token di Lexer). Namun, AI sempat keliru dan memberikan instruksi yang menyesatkan ketika mencoba memanggil variabel *scope*, karena AI mengasumsikannya sebagai sebuah *list* bernama `self.scopes`, padahal di program saya itu adalah sebuah *dictionary* bernama `self.scope.entries` di dalam objek. Kesalahan ini langsung saya ketahui ketika eksekusi kode memunculkan pesan `AttributeError` dan `TypeError`, yang kemudian memaksa saya untuk membuka kelas `Scope` dan meluruskan pemahaman AI.


