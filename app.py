import io
import os
import arabic_reshaper
from bidi.algorithm import get_display
import pandas as pd
import plotly.express as px
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
import streamlit as st

# ==========================================
# 0. إعدادات الصفحة والخطوط والخلفية المتداخلة
# ==========================================
st.set_page_config(page_title="نظام التقارير المالية المتكامل - Full IFRS", layout="wide")

# إضافة تأثير التدرج اللوني الخلفي (Gradient Background)
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #090d16 100%);
        background-attachment: fixed;
    }
    </style>
""", unsafe_allow_html=True)

ARABIC_FONT = None
font_path = 'Amiri-Regular.ttf'

if os.path.exists(font_path):
    try:
        pdfmetrics.registerFont(TTFont('ArabicFont', font_path))
        ARABIC_FONT = 'ArabicFont'
    except Exception:
        ARABIC_FONT = None

def ar(text):
    if text is None or pd.isna(text):
        return ''
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)

def suggest_ifrs_category(account_name):
    name = str(account_name).lower().strip()
    if any(w in name for w in ["أثاث", "سيار", "آلات", "مباني", "أراض", "معدات", "أصول ثابتة", "مجمع إهلاك", "مجمع اهلاك", "تجهيزات", "عقارات", "equipment", "asset", "building", "vehicle", "furniture", "depreciation"]):
        return "إيضاح (1): الأصول غير المتداولة (Property, Plant & Equipment)"
    elif any(w in name for w in ["نقد", "بنك", "صندوق", "خزينة", "شبكة", "عهدة", "cash", "bank", "petty", "treasury"]):
        return "إيضاح (3): النقدية وما في حكمها (Cash & Cash Equivalents)"
    elif any(w in name for w in ["عملاء", "عميل", "مدينون", "مخزون", "بضاعة", "مقدماً", "مقدم", "أوراق قبض", "ارباح مستحقة", "ذمم مدينة", "ارصدة مدينة", "مخصص ديون", "receivable", "inventory", "debtor", "prepaid", "allowance"]):
        return "إيضاح (2): الأصول المتداولة (باستثناء النقدية)"
    elif any(w in name for w in ["مورد", "دائنون", "مستحق", "ذمم دائنة", "أوراق دفع", "ضريبة", "زكاة", "تأمين", "ضريبة القيمة المضافة", "ارصدة دائنة", "payable", "creditor", "tax", "vat", "accrued"]):
        return "إيضاح (6): الالتزامات المتداولة (Current Liabilities)"
    elif any(w in name for w in ["قرض طويل", "مكافأة نهاية الخدمة", "مكافاة نهاية الخدمة", "التزام طويل", "loan", "end of service", "long term"]):
        return "إيضاح (5): الالتزامات غير المتداولة (Non-Current Liabilities)"
    elif any(w in name for w in ["رأس المال", "راس المال", "جاري الشريك", "equity", "capital"]):
        return "إيضاح (4-أ): رأس المال (Share Capital)"
    elif any(w in name for w in ["أرباح مبقاة", "ارباح مبقاة", "أرباح مدورة", "ارباح مدورة", "احتياطي", "retained"]):
        return "إيضاح (4-ب): الأرباح المبقاة / المدورة (Retained Earnings)"
    elif any(w in name for w in ["إيراد", "ايراد", "مبيعات", "خدمات تقديم", "مردودات مبيعات", "خصم مسموح", "revenue", "sales", "income"]):
        return "إيضاح (7): الإيرادات من العقود مع العملاء (Revenue)"
    elif any(w in name for w in ["تكلفة المبيعات", "تكلفة الإيرادات", "تكلفة الايرادات", "مشتريات", "مواد خام", "خصم مكتسب", "cogs", "cost"]):
        return "إيضاح (8): تكلفة الإيرادات (Cost of Sales)"
    elif any(w in name for w in ["راتب", "رواتب", "إيجار", "ايجار", "كهرباء", "ماء", "تسويق", "صيانة", "عمومية", "إدارية", "مصروف", "مصاريف", "هاتف", "اتصالات", "رسوم", "expense", "salary", "rent", "utility", "fee"]):
        return "إيضاح (9): المصاريف العمومية والإدارية (OPEX)"
    return "إيضاح (2): الأصول المتداولة (باستثناء النقدية)"

def generate_pdf_report(company_name, report_type, fiscal_year, pnl_df, bs_df, cf_df):
    if not ARABIC_FONT:
        raise ValueError("ملف الخط العربي (Amiri-Regular.ttf) غير متاح لتوليد ملف الـ PDF.")
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('ArabicTitle', parent=styles['Heading1'], fontName=ARABIC_FONT, alignment=1, fontSize=18, leading=22)
    subtitle_style = ParagraphStyle('ArabicSubTitle', parent=styles['Normal'], fontName=ARABIC_FONT, alignment=1, fontSize=11, leading=15)
    header_style = ParagraphStyle('ArabicHeader', parent=styles['Heading2'], fontName=ARABIC_FONT, alignment=2, fontSize=13, leading=17)
    cell_style = ParagraphStyle('ArabicCell', parent=styles['Normal'], fontName=ARABIC_FONT, alignment=2, fontSize=9, leading=12)

    story.append(Paragraph(ar(f'التقرير المالي المجمع - {company_name}'), title_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(ar(f'الفترة: {report_type} لعام {fiscal_year} | إطار التقارير الدولية (Full IFRS)'), subtitle_style))
    story.append(Spacer(1, 20))

    def build_pdf_table(df, title):
        elements = [Paragraph(ar(title), header_style), Spacer(1, 6)]
        table_data = []
        headers = [ar(col) for col in reversed(df.columns)]
        table_data.append(headers)

        for _, row in df.iterrows():
            row_data = []
            for val in reversed(row.values):
                formatted_val = f'{val:,.2f}' if isinstance(val, (int, float)) else ar(val)
                row_data.append(Paragraph(formatted_val, cell_style))
            table_data.append(row_data)

        num_cols = len(df.columns)
        printable_width = 535.0
        col_widths = [max(printable_width - (110.0 * (num_cols - 1)), 150.0)] + [110.0] * (num_cols - 1) if num_cols > 1 else [printable_width]

        t = Table(table_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F2937')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 14))
        return elements

    story.extend(build_pdf_table(pnl_df, '1. قائمة الدخل الشامل'))
    story.extend(build_pdf_table(bs_df, '2. قائمة المركز المالي'))
    story.extend(build_pdf_table(cf_df, '3. قائمة التدفقات النقدية (IAS 7)'))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================
# 1. إدارة المستخدمين وتسجيل الدخول
# ==========================================
if "users_db" not in st.session_state:
    st.session_state["users_db"] = {
        "abedear": "051002"
    }

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["current_user"] = ""

if not st.session_state["authenticated"]:
    st.title("🔐 تسجيل الدخول إلى نظام التقارير المالية")
    col1, col2 = st.columns([1, 2])
    with col1:
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        if st.button("تسجيل الدخول", use_container_width=True):
            users = st.session_state["users_db"]
            if username in users and users[username] == password:
                st.session_state["authenticated"] = True
                st.session_state["current_user"] = username
                st.success(f"مرحباً بك {username}!")
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة")
    st.stop()

# ==========================================
# 2. إعدادات الشريط الجانبي (مع دعم ملف المقارنة)
# ==========================================
st.sidebar.title('⚙️ إعدادات التقرير والشركة')
st.sidebar.write(f"👤 المستخدم الحالي: **{st.session_state['current_user']}**")

if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state["authenticated"] = False
    st.session_state["current_user"] = ""
    st.rerun()

company_name = st.sidebar.text_input('اسم شركة العميل', value='شركة التجربة المحدودة')
report_type = st.sidebar.selectbox('نوع الفترة المالية', ['تقرير سنوي', 'تقرير ربع سنوي (Q1)', 'تقرير ربع سنوي (Q2)', 'تقرير ربع سنوي (Q3)', 'تقرير ربع سنوي (Q4)', 'تقرير شهري'])
fiscal_year = st.sidebar.selectbox('السنة المالية الحالية', [2026, 2025, 2024])

st.title(f'📊 القوائم المالية الأربع والإيضاحات المتممة - {company_name}')
st.caption(f'التقرير: **{report_type}** لعام **{fiscal_year}** | معايير الإبلاغ المالي الدولية **Full IFRS**')

st.sidebar.markdown('---')
st.sidebar.subheader('📁 ملفات ميزان المراجعة')
uploaded_file = st.sidebar.file_uploader('1. ميزان مراجعة السنة الحالية (Excel / CSV)', type=['xlsx', 'csv'])
uploaded_file_prev = st.sidebar.file_uploader('2. ميزان مراجعة السنة السابقة للمقارنة (اختياري)', type=['xlsx', 'csv'])

st.sidebar.markdown('---')
st.sidebar.subheader('📌 أرصدة بداية الفترة (للتدفقات IAS 7)')
beg_cash = st.sidebar.number_input('1. النقدية وما في حكمها (أول المدة)', value=50000.0)
beg_c_assets = st.sidebar.number_input('2. الأصول المتداولة غير النقدية (أول المدة)', value=120000.0)
beg_c_liab = st.sidebar.number_input('3. الالتزامات المتداولة (أول المدة)', value=80000.0)
beg_nc_assets = st.sidebar.number_input('4. الأصول غير المتداولة (أول المدة)', value=300000.0)
beg_nc_liab = st.sidebar.number_input('5. الالتزامات غير المتداولة (أول المدة)', value=100000.0)
beg_capital = st.sidebar.number_input('6. رأس المال (أول المدة)', value=100000.0)
beg_retained = st.sidebar.number_input('7. الأرباح المبقاة (أول المدة)', value=20000.0)

st.sidebar.markdown('---')
st.sidebar.subheader('📌 التسويات غير النقدية')
depreciation = st.sidebar.number_input('مصروف الإهلاك للفترة', value=15000.0)
dividends = st.sidebar.number_input('توزيعات الأرباح / المسحوبات', value=10000.0)

# ==========================================
# دالة معالجة ميزان المراجعة
# ==========================================
def process_trial_balance(file, is_demo=False, demo_type="current"):
    if file:
        if file.name.endswith('.csv'):
            d_frame = pd.read_csv(file)
        else:
            d_frame = pd.read_excel(file)
    else:
        if demo_type == "current":
            d_frame = pd.DataFrame({
                'اسم الحساب': ['النقد بالبنك', 'العملاء', 'المخزون', 'الأثاث والمعدات', 'الموردون', 'مصاريف مستحقة', 'قرض طويل الأجل', 'رأس المال', 'إيراد المبيعات', 'تكلفة المبيعات', 'رواتب وأجور', 'إيجار المقر'],
                'مدين': [85000, 140000, 60000, 285000, 0, 0, 0, 0, 0, 120000, 45000, 15000],
                'دائن': [0, 0, 0, 0, 95000, 10000, 100000, 100000, 440000, 0, 0, 0]
            })
        else:
            d_frame = pd.DataFrame({
                'اسم الحساب': ['النقد بالبنك', 'العملاء', 'المخزون', 'الأثاث والمعدات', 'الموردون', 'مصاريف مستحقة', 'قرض طويل الأجل', 'رأس المال', 'إيراد المبيعات', 'تكلفة المبيعات', 'رواتب وأجور', 'إيجار المقر'],
                'مدين': [50000, 110000, 50000, 250000, 0, 0, 0, 0, 0, 100000, 40000, 12000],
                'دائن': [0, 0, 0, 0, 80000, 80000, 100000, 100000, 380000, 0, 0, 0]
            })
    
    acc_c, deb_c, cre_c = 'اسم الحساب', 'مدين', 'دائن'
    d_frame[deb_c] = pd.to_numeric(d_frame[deb_c], errors='coerce').fillna(0)
    d_frame[cre_c] = pd.to_numeric(d_frame[cre_c], errors='coerce').fillna(0)
    d_frame['Net_Debit_Focus'] = d_frame[deb_c] - d_frame[cre_c]
    d_frame['Net_Credit_Focus'] = d_frame[cre_c] - d_frame[deb_c]
    return d_frame, acc_c, deb_c, cre_c

df, account_col, debit_col, credit_col = process_trial_balance(uploaded_file, demo_type="current")
if not uploaded_file:
    st.info('ℹ️ يتم استخدام ميزان مراجعة تجريبي حالياً للسنة الحالية لعدم رفع ملف.')

ifrs_categories = [
    "إيضاح (1): الأصول غير المتداولة (Property, Plant & Equipment)",
    "إيضاح (2): الأصول المتداولة (باستثناء النقدية)",
    "إيضاح (3): النقدية وما في حكمها (Cash & Cash Equivalents)",
    "إيضاح (4-أ): رأس المال (Share Capital)",
    "إيضاح (4-ب): الأرباح المبقاة / المدورة (Retained Earnings)",
    "إيضاح (5): الالتزامات غير المتداولة (Non-Current Liabilities)",
    "إيضاح (6): الالتزامات المتداولة (Current Liabilities)",
    "إيضاح (7): الإيرادات من العقود مع العملاء (Revenue)",
    "إيضاح (8): تكلفة الإيرادات (Cost of Sales)",
    "إيضاح (9): المصاريف العمومية والإدارية (OPEX)"
]

file_key = f"mapping_demo_{account_col}" if not uploaded_file else f"mapping_{uploaded_file.name}"
if file_key not in st.session_state:
    init_df = df[[account_col, 'Net_Debit_Focus', 'Net_Credit_Focus']].copy()
    init_df['IFRS_Category'] = init_df[account_col].apply(suggest_ifrs_category)
    st.session_state[file_key] = init_df

edited_df = st.data_editor(
    st.session_state[file_key],
    column_config={
        'IFRS_Category': st.column_config.SelectboxColumn('تصنيف IFRS والإيضاح المتمم', options=ifrs_categories, required=True),
        'Net_Debit_Focus': st.column_config.NumberColumn('صافي الحركة (مدين - دائن)', format='%.2f SAR'),
        'Net_Credit_Focus': st.column_config.NumberColumn('صافي الحركة (دائن - مدين)', format='%.2f SAR')
    },
    disabled=[account_col, 'Net_Debit_Focus', 'Net_Credit_Focus'],
    hide_index=True,
    use_container_width=True
)

df_prev, _, _, _ = process_trial_balance(uploaded_file_prev, demo_type="previous")
df_prev['IFRS_Category'] = df_prev[account_col].apply(suggest_ifrs_category)

# ==========================================
# 4. حساب وتجهيز القوائم المالية (الحالية والسابقة)
# ==========================================
def calculate_financials(target_df):
    nc_a = target_df[target_df['IFRS_Category'] == "إيضاح (1): الأصول غير المتداولة (Property, Plant & Equipment)"]['Net_Debit_Focus'].sum()
    c_a_ex = target_df[target_df['IFRS_Category'] == "إيضاح (2): الأصول المتداولة (باستثناء النقدية)"]['Net_Debit_Focus'].sum()
    cash_tb = target_df[target_df['IFRS_Category'] == "إيضاح (3): النقدية وما في حكمها (Cash & Cash Equivalents)"]['Net_Debit_Focus'].sum()
    cos_val = target_df[target_df['IFRS_Category'] == "إيضاح (8): تكلفة الإيرادات (Cost of Sales)"]['Net_Debit_Focus'].sum()
    opex_val = target_df[target_df['IFRS_Category'] == "إيضاح (9): المصاريف العمومية والإدارية (OPEX)"]['Net_Debit_Focus'].sum()

    tb_cap = target_df[target_df['IFRS_Category'] == "إيضاح (4-أ): رأس المال (Share Capital)"]['Net_Credit_Focus'].sum()
    tb_ret = target_df[target_df['IFRS_Category'] == "إيضاح (4-ب): الأرباح المبقاة / المدورة (Retained Earnings)"]['Net_Credit_Focus'].sum()
    nc_l = target_df[target_df['IFRS_Category'] == "إيضاح (5): الالتزامات غير المتداولة (Non-Current Liabilities)"]['Net_Credit_Focus'].sum()
    c_l = target_df[target_df['IFRS_Category'] == "إيضاح (6): الالتزامات المتداولة (Current Liabilities)"]['Net_Credit_Focus'].sum()
    rev_val = target_df[target_df['IFRS_Category'] == "إيضاح (7): الإيرادات من العقود مع العملاء (Revenue)"]['Net_Credit_Focus'].sum()

    gp = rev_val - cos_val
    ni = gp - opex_val
    tot_assets = nc_a + c_a_ex + cash_tb
    cap = tb_cap if tb_cap != 0 else beg_capital
    ret = tb_ret if tb_ret != 0 else beg_retained
    ret_earn = ret + ni - dividends
    tot_eq = cap + ret_earn
    tot_liab = nc_l + c_l
    tot_eq_l = tot_eq + tot_liab

    return rev_val, cos_val, gp, opex_val, ni, nc_a, c_a_ex, cash_tb, tot_assets, cap, ret_earn, tot_eq, nc_l, c_l, tot_eq_l

rev, cos, gross_profit, opex, net_income, end_nc_assets, end_c_assets_ex_cash, end_cash_tb, total_assets, capital, retained_earnings, total_equity, end_nc_liab, end_c_liab, total_equity_liab = calculate_financials(edited_df)
prev_rev, prev_cos, prev_gp, prev_opex, prev_ni, prev_nc_a, prev_c_a_ex, prev_cash, prev_tot_assets, prev_cap, prev_ret_earn, prev_tot_eq, prev_nc_l, prev_c_l, prev_tot_eq_l = calculate_financials(df_prev)

pnl_df = pd.DataFrame({
    'البند (IFRS)': ['الإيرادات من العقود مع العملاء', 'تكلفة المبيعات', 'مجمل الربح', 'المصاريف التشغيلية والإدارية', 'صافي الربح للفترة'],
    'رقم الإيضاح': ['إيضاح (7)', 'إيضاح (8)', '-', 'إيضاح (9)', '-'],
    f'المبلغ ({fiscal_year} SAR)': [rev, -cos, gross_profit, -opex, net_income],
    f'المبلغ ({fiscal_year-1} SAR)': [prev_rev, -prev_cos, prev_gp, -prev_opex, prev_ni]
})
pnl_df['التغير (SAR)'] = pnl_df[f'المبلغ ({fiscal_year} SAR)'] - pnl_df[f'المبلغ ({fiscal_year-1} SAR)']
pnl_df['نسبة التغير (%)'] = (pnl_df['التغير (SAR)'] / pnl_df[f'المبلغ ({fiscal_year-1} SAR)'].abs() * 100).fillna(0).round(2)

bs_df = pd.DataFrame({
    'عناصر المركز المالي': [
        'الأصول غير المتداولة', 'الأصول المتداولة (غير النقدية)', 'النقدية وما في حكمها', 'إجمالي الأصول',
        'رأس المال', 'الأرباح المبقاة (شاملة ربح الفترة)', 'إجمالي حقوق الملكية',
        'الالتزامات غير المتداولة', 'الالتزامات المتداولة', 'إجمالي الالتزامات وحقوق الملكية'
    ],
    'رقم الإيضاح': ['إيضاح (1)', 'إيضاح (2)', 'إيضاح (3)', '-', 'إيضاح (4-أ)', 'إيضاح (4-ب)', '-', 'إيضاح (5)', 'إيضاح (6)', '-'],
    f'المبلغ ({fiscal_year} SAR)': [end_nc_assets, end_c_assets_ex_cash, end_cash_tb, total_assets, capital, retained_earnings, total_equity, end_nc_liab, end_c_liab, total_equity_liab],
    f'المبلغ ({fiscal_year-1} SAR)': [prev_nc_a, prev_c_a_ex, prev_cash, prev_tot_assets, prev_cap, prev_ret_earn, prev_tot_eq, prev_nc_l, prev_c_l, prev_tot_eq_l]
})
bs_df['التغير (SAR)'] = bs_df[f'المبلغ ({fiscal_year} SAR)'] - bs_df[f'المبلغ ({fiscal_year-1} SAR)']
bs_df['نسبة التغير (%)'] = (bs_df['التغير (SAR)'] / bs_df[f'المبلغ ({fiscal_year-1} SAR)'].abs() * 100).fillna(0).round(2)

eq_df = pd.DataFrame({
    'البيان': ['رصيد بداية الفترة', 'صافي ربح الفترة', 'توزيعات الأرباح / المسحوبات', 'رصيد نهاية الفترة'],
    'رأس المال (SAR)': [capital, 0, 0, capital],
    'الأرباح المبقاة (SAR)': [retained_earnings - net_income + dividends, net_income, -dividends, retained_earnings],
    'إجمالي حقوق الملكية (SAR)': [capital + retained_earnings - net_income + dividends, net_income, -dividends, total_equity]
})

delta_c_assets = end_c_assets_ex_cash - beg_c_assets
delta_c_liab = end_c_liab - beg_c_liab
delta_nc_assets = end_nc_assets - beg_nc_assets
delta_nc_liab = end_nc_liab - beg_nc_liab

operating_cf = net_income + depreciation - delta_c_assets + delta_c_liab
investing_cf = -(delta_nc_assets + depreciation)
financing_cf = delta_nc_liab - dividends
net_cash_change = operating_cf + investing_cf + financing_cf
calculated_ending_cash = beg_cash + net_cash_change

cf_df = pd.DataFrame({
    'بيان التدفقات النقدية (IAS 7)': [
        'صافي الربح قبل الضريبة والزكاة', 'تعديل: مصروف الإهلاك (عنصر غير نقدي)',
        'التغير في الأصول المتداولة (باستثناء النقدية)', 'التغير في الالتزامات المتداولة',
        'صافي التدفقات النقدية من الأنشطة التشغيلية', 'صافي التدفقات النقدية من الأنشطة الاستثمارية',
        'صافي التدفقات النقدية من الأنشطة التمويلية', 'صافي التغير في النقدية خلال الفترة',
        'النقدية وما في حكمها - بداية الفترة', 'النقدية وما في حكمها - نهاية الفترة (المحسوبة)'
    ],
    'المبلغ (SAR)': [net_income, depreciation, -delta_c_assets, delta_c_liab, operating_cf, investing_cf, financing_cf, net_cash_change, beg_cash, calculated_ending_cash]
})

# ==========================================
# 5. عرض التبويبات
# ==========================================
st.divider()

total_debit, total_credit = df[debit_col].sum(), df[credit_col].sum()
tb_diff = abs(total_debit - total_credit)
tb_is_balanced = tb_diff < 1.0

bs_diff = abs(total_assets - total_equity_liab)
bs_is_balanced = bs_diff < 1.0

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    '1️⃣ قائمة الدخل الشامل', '2️⃣ قائمة المركز المالي', '3️⃣ التغيرات في حقوق الملكية',
    '4️⃣ قائمة التدفقات النقدية', '📄 الإيضاحات المتممة (Notes)', '📈 الداشبورد والتحليل', '🔍 مركز الفحص والتدقيق', '👥 إدارة المستخدمين'
])

with tab1:
    st.subheader('قائمة الربح أو الخسارة والدخل الشامل الآخر مع المقارنة الزمنية')
    st.table(pnl_df)

with tab2:
    st.subheader('قائمة المركز المالي مع المقارنة الزمنية')
    st.table(bs_df)

with tab3:
    st.subheader('قائمة التغيرات في حقوق الملكية')
    st.table(eq_df)

with tab4:
    st.subheader('قائمة التدفقات النقدية (الطريقة غير المباشرة - IAS 7)')
    st.table(cf_df)

with tab5:
    st.subheader(f'الإيضاحات المتممة للقوائم المالية - {company_name}')
    for cat in ifrs_categories:
        with st.expander(f'📌 {cat}'):
            sub_df = edited_df[edited_df['IFRS_Category'] == cat]
            if not sub_df.empty:
                val_col = 'Net_Debit_Focus' if any(x in cat for x in ['الأصول', 'المصاريف', 'النقدية', 'تكلفة']) else 'Net_Credit_Focus'
                st.table(sub_df[[account_col, val_col]].rename(columns={val_col: 'الرصيد الصافي (SAR)'}))
            else:
                st.write('لا توجد تفاصيل حسابات.')

with tab6:
    st.subheader('مؤشرات الأداء والتحليل التنفيذي')
    k1, k2, k3, k4 = st.columns(4)
    k1.metric('هامش مجمل الربح', f'{(gross_profit/rev*100) if rev else 0:.1f}%')
    k2.metric('هامش صافي الربح', f'{(net_income/rev*100) if rev else 0:.1f}%')
    k3.metric('نسبة السيولة التداول', f'{((end_c_assets_ex_cash + end_cash_tb) / end_c_liab) if end_c_liab else 0:.2f}')
    k4.metric('رأس المال العامل', f'{((end_c_assets_ex_cash + end_cash_tb) - end_c_liab):,.0f} SAR')

    fig = px.bar(edited_df, x='IFRS_Category', y='Net_Debit_Focus', color='IFRS_Category', title='توزيع حركة الحسابات حسب الإيضاحات')
    st.plotly_chart(fig, use_container_width=True)

with tab7:
    st.subheader('🔍 مركز الفحص والتحقق من جودة التقارير')
    col_a, col_b = st.columns(2)
    col_a.success('✅ ميزان المراجعة متوازن') if tb_is_balanced else col_a.error(f'❌ عدم توازن ميزان المراجعة ({tb_diff:,.2f} SAR)')
    col_b.success('✅ الميزانية العمومية متوازنة') if bs_is_balanced else col_b.error(f'❌ عدم توازن الميزانية ({bs_diff:,.2f} SAR)')

with tab8:
    st.subheader('👥 إدارة حسابات النظام')
    col_u1, col_u2 = st.columns(2)
    
    with col_u1:
        st.markdown('### ➕ إضافة مستخدم جديد')
        new_username = st.text_input('اسم المستخدم الجديد')
        new_password = st.text_input('كلمة المرور للمستخدم الجديد', type='password')
        if st.button('إضافة المستخدم', use_container_width=True):
            if new_username in st.session_state['users_db']:
                st.error('⚠️ اسم المستخدم موجود بالفعل!')
            elif new_username and new_password:
                st.session_state['users_db'][new_username] = new_password
                st.success(f'✅ تم إضافة المستخدم ({new_username}) بنجاح!')
            else:
                st.warning('يرجى ملء كافة الحقول.')

    with col_u2:
        st.markdown(f'### ✏️ تعديل كلمة المرور ({st.session_state["current_user"]})')
        curr_user = st.session_state["current_user"]
        old_pass = st.text_input('كلمة المرور الحالية', type='password')
        new_pass_edit = st.text_input('كلمة المرور الجديدة', type='password')
        if st.button('تحديث كلمة المرور', use_container_width=True):
            if st.session_state['users_db'][curr_user] == old_pass:
                if new_pass_edit:
                    st.session_state['users_db'][curr_user] = new_pass_edit
                    st.success('✅ تم تغيير كلمة المرور بنجاح!')
                else:
                    st.warning('يرجى إدخال كلمة المرور الجديدة.')
            else:
                st.error('❌ كلمة المرور الحالية غير صحيحة!')

    st.markdown('---')
    st.markdown('### 📋 قائمة المستخدمين المسجلين حالياً')
    users_df = pd.DataFrame(list(st.session_state['users_db'].keys()), columns=['اسم المستخدم'])
    st.table(users_df)

# ==========================================
# 6. تصدير التقارير
# ==========================================
st.divider()
st.subheader('📥 تصدير حزمة التقارير المالية')
col_excel, col_pdf = st.columns(2)

with col_excel:
    buffer_excel = io.BytesIO()
    with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
        pnl_df.to_excel(writer, sheet_name='1- قائمة الدخل', index=False)
        bs_df.to_excel(writer, sheet_name='2- المركز المالي', index=False)
        eq_df.to_excel(writer, sheet_name='3- التغيرات في الملكية', index=False)
        cf_df.to_excel(writer, sheet_name='4- التدفقات النقدية', index=False)
        edited_df.to_excel(writer, sheet_name='5- تفاصيل الإيضاحات المتممة', index=False)
    buffer_excel.seek(0)
    st.download_button('🟢 تحميل التقرير الكامل (Excel)', data=buffer_excel, file_name=f'القوائم_{company_name}.xlsx', use_container_width=True)

with col_pdf:
    if ARABIC_FONT:
        pdf_data = generate_pdf_report(company_name, report_type, fiscal_year, pnl_df, bs_df, cf_df)
        st.download_button('🔴 تحميل التقرير المالي الرسمي (PDF)', data=pdf_data, file_name=f'التقرير_{company_name}.pdf', mime='application/pdf', use_container_width=True)
    else:
        st.warning('⚠️ يرجى إضافة ملف الخط Amiri-Regular.ttf لتفعيل تحميل الـ PDF.')