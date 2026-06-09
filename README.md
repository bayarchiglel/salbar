# Чиглэл ХХК — Бараа Каталог

GitHub Pages дээр ажилладаг бараа каталог систем.

## Тохируулах

Public GitHub Pages үнэгүй боловч public repo дээр үнэ болон барааны мэдээлэл ил харагдана. Энэ хувилбараас нөөц / stock мэдээллийг бүрэн хассан.

## Admin token

Admin page нь GitHub token-ийг browser-оос GitHub API руу илгээдэг client-side хэрэгсэл хэвээр байна. Token-ийг browser storage-д хадгалахгүй. Repo нэрийг л sessionStorage-д санана.

Зөвлөмж:

1. Fine-grained personal access token үүсгэ.
2. Repository access: зөвхөн энэ repo.
3. Permissions: Contents → Read and write.
4. Expiration: богино хугацаа.

Илүү найдвартай хувилбар бол жижиг backend эсвэл GitHub Actions admin workflow ашиглах.

## Засварууд

- Product data-г public хуудсуудад escape/DOM-safe байдлаар харуулна.
- PDF badge/filter зөвхөн manual_url байгаа үед ажиллана.
- Save хийх үед GitHub дээрх latest products.json-г дахин татаж, өөрчилсөн бараануудыг merge хийж commit хийнэ.
- Google Drive PDF link-ээс file ID parse хийж preview/download URL тусад нь үүсгэнэ.
- Admin дээр нэр, үнэ, ангилал, гарал, бренд, марк, онцлог, хэмжээ, жин, хүчдэл, кВт, PDF link засна.
- Шинэ бараа нэмэх боломж нэмэгдсэн.

## PDF

Google Drive дээр PDF upload хийгээд Share → Anyone with the link болгоно. Admin дээр PDF талбарт Drive link оруулна.

---
Чиглэл ХХК | info@chiglel.mn | +976 7611 5333
