# Chuẩn mô hình dữ liệu bảo hiểm quốc tế dùng để đối chiếu

Tài liệu tra cứu ngày 07/10/2026. Mục nào ghi **(chưa xác minh)** là chưa đọc được bản gốc.

## Mô hình v2 so với các chuẩn

| Bảng v2 | IBM IIW / IAA | ACORD P&C | Kimball (DWT 3e, Ch.16) | OMG P&C 1.0 / Microsoft CDM | IFRS 17 / Solvency II / NAIC |
|---|---|---|---|---|---|
| `core.policy` | Agreement (Insurance Agreement) | Policy (PolicyNumber, ContractTerm, LOBCd) | Policy (degenerate dimension) | OMG: Policy · CDM: Policy | Contract → portfolio / group |
| `core.policy_transaction` | Event + Financial Transaction | `BusinessPurposeTypeCd`: NBS / PCH / XLC / REI / RWL | Policy Transaction fact + Transaction Type dim | CDM: **PolicyTransaction** | — |
| `core.transaction_coverage` | Agreement component ↔ Product component; Money Provision | **Coverage**: `CoverageCd`, `WrittenAmt`, **`NetChangeAmt`** (khoản thay đổi phí của giao dịch) | Grain coverage × covered item | OMG: Policy Coverage Part / **Policy Coverage Detail**; CDM: Coverage | Written premium (NAIC Part 1B) |
| `core.coinsurance_share` | Agreement + Party role (insurer) | Thị trường subscription: Written/Signed Line, `leadUnderwriter` (JMRC). **Không phải** `CoinsurancePct` | — | OMG: Policy Amount (Direct / Assumed / Ceded); Oracle OIDF: "Insurance and Reinsurance Participation"; CDM: Insurer | Gross vs own share |
| `core.revenue_allocation` | Account / Organization (Party) | — | Allocated facts | — | — |
| `ref.customer` | Party + Role Player | Insured / Party | Policyholder dim | OMG: Party, Agreement Party Role | — |
| `ref.channel` / `ref.partner` | Party role Intermediary | Producer (`ProducerRoleCd`) | Agent dim | CDM: Agency, Agent, BrokerAgency | Commission |
| `ref.line_of_business` / `ref.product` | Category; Specification, Product | `LOBCd`; Product Model | Coverage dim (supertype/subtype) | CDM: LOB, CoverageLOB, PolicyProduct | **Solvency II LoB 1–12**; NAIC LOB |
| `ref.fx_rate` | Financial Transaction / Account | Currency code | **Multiple currencies**: lưu cả nguyên tệ và tiền chuẩn | — | — |

## Đã áp dụng vào v2

- `ref.transaction_type.acord_business_purpose_cd`: NEW→NBS, RENEW→RWL, các loại SĐBS và REFUND→PCH, CANCEL→XLC.
- `ref.product.solvency2_lob`: ánh xạ sang Solvency II LoB (Delegated Regulation 2015/35, Annex I):

  | Sản phẩm v2 | Solvency II LoB |
  |---|---|
  | TNDS bắt buộc | (4) Motor vehicle liability |
  | Vật chất xe | (5) Other motor |
  | Sức khỏe | (1) Medical expense |
  | Tai nạn, sinh mạng | (2) Income protection — **suy luận** |
  | Du lịch | (1) Medical expense — **suy luận** |
  | Tài sản, cháy nổ | (7) Fire and other damage to property |

- `core.transaction_coverage.premium_orig` lưu **phần thay đổi phí của từng giao dịch**, tương đương `NetChangeAmt` của ACORD.

## Nguồn

**IBM**
- IIW brochure GIM v8.5: https://public.dhe.ibm.com/software/data/sw-library/industry-models/brochures/IBM_Insurance_Information_Warehouse_GIMv85.pdf
- IAA poster: https://public.dhe.ibm.com/software/data/mdm/pdf/IAA_Poster_2006.pdf

**ACORD**
- Reference Architecture: https://www.acord.org/standards-architecture/reference-architecture
- P&C Data Standards: https://www.acord.org/standards-architecture/acord-data-standards/Property_Casualty_Data_Standards
- Mã giao dịch (model viewer bên thứ ba): https://modelviewers.pilotfishtechnology.com/modelviewers/ACORD-PCS/model/codelists/CycleBusinessPurpose.html
- Whitespace JMRC spec (subscription market): https://apidocs.whitespace.co.uk/JMRC%20ACORD%20Specification%20V0.5%20-%20Defined%20Data.pdf

**Kimball**
- InsureCo case: https://www.kimballgroup.com/1995/12/data-warehouse-insurance/
- Multiple currencies: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/multiple-currencies/
- Supertype/subtype: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/supertype-subtype-heterogeneous/
- Số trang Chương 16: **(chưa xác minh)**

**Các mô hình ngành khác**
- OMG P&C Data Model 1.0: https://www.omg.org/spec/PC/1.0/About-PC
- Microsoft CDM P&C: https://learn.microsoft.com/en-us/common-data-model/schema/core/industrycommon/financialservices/propertyandcasualtydatamodel/overview
- Oracle Insurance Data Foundation: https://www.oracle.com/a/ocom/docs/industries/financial-services/insurance-data-warehouse-ds.pdf

**Kế toán và giám sát**
- IFRS 17: https://www.iasplus.com/en/standards/ifrs/ifrs-17
- Ví dụ PAA của IFRS Foundation: https://www.ifrs.org/content/dam/ifrs/supporting-implementation/ifrs-17/premium-allocation-approach-example.pdf
- Solvency II Annex I: https://www.legislation.gov.uk/eur/2015/35/annex/I/adopted

## Dataset mẫu public

Đây là các dataset mẫu của dự án. Chúng chỉ dùng để **chứng minh cấu trúc**, tức dữ liệu bảo hiểm thật trông ra sao. Chúng **không** dùng để lấy hay hiệu chỉnh số; mọi con số đều lấy theo thị trường Việt Nam, xem [market_data.md](market_data.md). Chi tiết từng tham số xem `docs/Logic_Sinh_Du_Lieu.html`, mục "Dataset mẫu".

| Dataset | Cấu trúc đã đọc (tra ngày 16/10/2026) | Chứng minh cho |
|---|---|---|
| CASdatasets `fremotor1prem0304a/b/c` (GPL) — https://github.com/dutangc/CASdatasets/blob/master/man-md/fremotor1prem0304a.md | 30 cột. Phí năm theo từng quyền lợi trên cùng hợp đồng: `PremTPLM` (TNDS bắt buộc), `PremTPLV` (TNDS tự nguyện), `PremDamAll` (thiệt hại vật chất), `PremFire`, `PremTheft`… và `PremTot`. Có thêm `Channel`, `Region`, `Year` | Một hợp đồng có nhiều dòng phí theo sản phẩm (`core.transaction_coverage`). Bán kèm vật chất xe + TNDS bắt buộc. TNDS tự nguyện tách riêng. Kênh là chiều của hợp đồng |
| Kaggle Travel Insurance (ODbL) — https://www.kaggle.com/datasets/mhdzahier/travel-insurance | `Agency Type` (Airlines / Travel Agency), `Distribution Channel` (Online / Offline), `Duration`, `Net Sales` (có giá trị âm), `Commision (in value)`. Cấu trúc được đọc trên bản trích 100 dòng công khai trên GitHub | Đối tác du lịch là hãng bay / đại lý du lịch. Hoàn phí là số âm. Hoa hồng là cột riêng, có dòng bằng 0. Thời hạn tính theo ngày chuyến đi |
| CAS Loss Reserving Database — https://www.casact.org/publications-research/research/research-resources/loss-reserving-data-pulled-naic-schedule-p | 6 nghiệp vụ × công ty × năm. `EarnedPremDIR` (direct & assumed), `EarnedPremCeded`, `EarnedPremNet` | Phí toàn bộ khác phần công ty giữ lại, nên phải tách phần của công ty. Phí tổng hợp theo nghiệp vụ × năm |
| CASdatasets `freMTPL2freq` / `freMTPL2sev` — https://dutangc.github.io/CASdatasets/reference/freMTPL.html | 677.991 hợp đồng TNDS xe, phần lớn quan sát trong 1 năm. `IDpol`, `Exposure` (năm), `ClaimNb`, `Region`, `Area`, `Density` | TNDS là nghiệp vụ "rất nhiều đơn nhỏ", thời hạn 1 năm. Vùng là thuộc tính của hợp đồng |
| UCI Insurance Company Benchmark (COIL 2000) — https://archive.ics.uci.edu/dataset/125/insurance+company+benchmark+coil+2000 | Mỗi khách hàng có phân khúc (`MOSHOOFD` / `MOSTYPE`), cùng mức phí và số hợp đồng theo từng loại sản phẩm (`PPERSAUT` xe, `PBRAND` cháy, `PPERSONG` tai nạn, `PLEVEN` nhân thọ…) | Phân khúc khách hàng. Một khách giữ nhiều sản phẩm (bán chéo) |
| Synthea — https://github.com/synthetichealth/synthea/wiki/CSV-File-Data-Dictionary | Bộ sinh dữ liệu "realistic but not real" theo cấu hình thống kê công khai. `payer_transitions` có `Start_Year` / `End_Year` và `Ownership` (Self / Guardian / Spouse) | Tiền lệ phương pháp sinh dữ liệu. Bên mua có thể khác người được bảo hiểm. Quyền lợi bảo hiểm nối tiếp theo năm |
| CMS Medicare DE-SynPUF — https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files | Dữ liệu giả lập giữ nguyên định dạng và tên biến của dữ liệu thật; CMS nói rõ giá trị suy luận rất hạn chế | Tiền lệ: giữ cấu trúc thật, nhưng số không dùng để suy luận |

**Đã xem xét nhưng không dùng:**
- SOA 2015 VBT: bảng tử vong cho bảo hiểm nhân thọ, không thuộc phạm vi.
- RAA ChainLadder: tam giác bồi thường dùng để ước tính dự phòng; POC không có bồi thường.
- Phần bồi thường của freMTPL2sev, CMS và Synthea: ngoài phạm vi doanh thu phí.
