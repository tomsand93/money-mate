# MoneyMate AI - Smart Expense Tracker 💰🤖

**Version 2.0** - AI-powered expense tracking with financial planning features

## 🌟 New Features

### 1. **AI-Powered Categorization**
- Automatic expense categorization using Ollama (local AI model)
- Learning from user corrections
- Fallback to keyword matching when AI is unavailable
- Confidence-based categorization with user prompts for uncertain cases

### 2. **50/30/20 Rule Analysis**
- Automatic classification of expenses into:
  - **50% Needs** (צרכים): Supermarket, Transportation, Health, Bills
  - **30% Wants** (רצונות): Dining out, Entertainment, Shopping, Travel
  - **20% Investment** (חיסכון והשקעות): Calculated from savings
- Visual progress bars showing adherence to goals
- Interactive pie charts for needs/wants/invest distribution

### 3. **Smart Recommendations**
- Personalized savings suggestions based on spending patterns
- Category-specific advice (eating out, subscriptions, transportation)
- Goal tracking and progress monitoring
- Positive reinforcement for good financial habits

### 4. **Modern Web UI**
- Beautiful, responsive Flask web application
- Hebrew RTL support with modern design
- Interactive dashboards with Chart.js visualizations
- Mobile-friendly interface

### 5. **Investment Tracking**
- Dedicated section for savings and investment goals
- Real-time calculation of savings rate
- Comparison to 50/30/20 targets
- Visual indicators for financial health

## 🚀 Quick Start

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/tomsand93/MoneyMate.git
cd MoneyMate
git checkout feature/ai-financial-planning
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install Ollama (for AI features):**
   - Download from [ollama.ai](https://ollama.ai)
   - Install and run:
   ```bash
   ollama run llama3.2
   ```

### Running the Application

**Web UI (Recommended):**
```bash
python app.py
```
Then open your browser to: `http://127.0.0.1:5000`

**Command Line (Legacy):**
```bash
python main.py
```

## 📊 Usage

### 1. Upload Credit Card Files
- Navigate to "העלאת קובץ" (Upload)
- Select your Excel file from credit card statement
- File naming convention: `transactions_MM_YYYY.xlsx`
- Click upload - AI will automatically categorize!

### 2. View Dashboard
- Main dashboard shows latest month
- Summary cards for income, expenses, savings
- 50/30/20 rule analysis with visual indicators
- Smart recommendations for saving money
- Interactive charts and graphs

### 3. Browse Reports
- View all monthly reports
- Detailed breakdown by category
- Top 10 biggest expenses
- Track progress over time

### 4. Settings
- Check AI status (Ollama availability)
- View categories and keywords
- See 50/30/20 rule configuration
- Installation instructions

## 🎨 Features in Detail

### AI Categorization
The AI categorizer uses a three-tier approach:
1. **User corrections** - Highest priority (100% confidence)
2. **Keyword matching** - Fast and reliable (95% confidence)
3. **AI inference** - For new/unknown expenses (variable confidence)

When confidence < 70%, the system can prompt user for verification.

### Financial Analysis

**Needs (50%):**
- סופרמרקט (Supermarket)
- תחבורה (Transportation)
- בריאות (Health)
- חשבונות ומנויים (Bills & Subscriptions)

**Wants (30%):**
- אוכל בחוץ (Dining out)
- בילויים (Entertainment)
- ביגוד והנעלה (Clothing)
- קניות אונליין (Online shopping)
- טיפוח אישי (Personal care)
- טיפוס וספורט (Climbing & Sports)
- נסיעות וטיולים (Travel)

**Investment/Savings (20%):**
- Calculated as: Income - (Needs + Wants)
- Should be at least 20% of income

### Recommendations Engine

The system generates personalized recommendations by:
- Analyzing spending patterns
- Identifying high-percentage categories
- Suggesting specific areas to reduce
- Calculating potential savings
- Providing actionable advice

Example recommendations:
- "🍽️ Eating out: ₪2,500 (12% of income). 30% reduction would save ₪750/month!"
- "📱 Check your subscriptions - you might have unused ones. You spend ₪450 on subscriptions."
- "✅ Great job! You're maintaining a good balance between needs and wants!"

## 📁 Project Structure

```
expance/
├── app.py                      # Flask web application
├── main.py                     # CLI interface (legacy)
├── ai_categorizer.py           # AI categorization engine
├── financial_analyzer.py       # 50/30/20 analysis & recommendations
├── expense_processor.py        # Excel processing
├── database.py                 # SQLite database
├── report_generator.py         # Report generation
├── dashboard_generator.py      # HTML dashboard (legacy)
├── config_ai.json             # AI configuration
├── config.json                # Legacy configuration
├── templates/                 # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── upload.html
│   ├── reports.html
│   ├── report_detail.html
│   ├── settings.html
│   └── welcome.html
├── static/
│   └── css/
│       └── style.css          # Modern styling
├── input_files/               # Credit card Excel files
├── reports/                   # Generated reports
└── requirements.txt           # Python dependencies
```

## 🔧 Configuration

Edit `config_ai.json` to customize:

```json
{
  "ai": {
    "model": "llama3.2",
    "confidence_threshold": 0.7,
    "enable_learning": true,
    "user_corrections_file": "ai_learning.json"
  },
  "need_want_invest": {
    "needs": ["סופרמרקט", "תחבורה", "בריאות", "חשבונות ומנויים"],
    "wants": ["אוכל בחוץ", "בילויים", ...],
    "target_percentages": {
      "needs": 50,
      "wants": 30,
      "invest": 20
    }
  }
}
```

## 🆚 Version Comparison

| Feature | v1.0 (master) | v2.0 (AI) |
|---------|---------------|-----------|
| Interface | CLI | Web UI |
| Categorization | Keywords only | AI + Keywords |
| Financial Planning | Basic | 50/30/20 Rule |
| Recommendations | None | Smart suggestions |
| Learning | No | Yes (user corrections) |
| Charts | Static HTML | Interactive web |
| Mobile Support | No | Yes |

## 🤝 Contributing

This is a personal expense tracker, but feel free to fork and customize!

## 📝 License

Private project - for personal use

## 🙏 Credits

- **AI Model**: Ollama + Llama 3.2
- **Charts**: Chart.js
- **Web Framework**: Flask
- **Data Processing**: Pandas
- **UI Design**: Custom CSS with modern gradients

---

**Happy tracking! 💰📊**

Need help? Check the Settings page for installation instructions.
