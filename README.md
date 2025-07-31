# Discord Psychological Analyzer

A tool for extracting Discord server messages and performing psychological analysis on user communication patterns using AI.

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Always ensure you have proper authorization before analyzing Discord servers or user data. Respect privacy and follow Discord's Terms of Service and applicable laws.

## Features

- Extract messages from Discord servers
- Analyze user communication patterns
- Generate psychological insights using DeepSeek AI
- Export detailed analysis reports

## Prerequisites

- Python 3.7+
- Discord account with access to target server
- DeepSeek API key
- Required Python packages (see requirements.txt)

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/pentestfunctions/psychoshit.git
cd psychoshit
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
DISCORD_USER_TOKEN=""
SERVER_ID=""
DEEPSEEK_API_KEY=""
```

#### Getting Your Discord Token

1. Open Discord in a web browser
2. Open Developer Tools (F12)
3. Go to the Application/Storage tab
4. Navigate to Cookies
5. Find the `token` cookie and copy its value
6. Paste the token into your `.env` file

#### Getting Server ID

1. Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
2. Right-click on the server name (not a channel within the server)
3. Select "Copy ID"
4. Paste the server ID into your `.env` file

#### Getting DeepSeek API Key

1. Visit [DeepSeek](https://www.deepseek.com/)
2. Create an account and generate an API key
3. Add the API key to your `.env` file

## Usage

### Step 1: Extract Messages

Run the message extractor to download all messages from the specified Discord server:

```bash
python discord_server_extractor.py
```

This will extract and save all messages from the server specified in your `.env` file.

#### Optional Parameters

You can customize the extraction with additional parameters:

```bash
# Extract only specific channels
python discord_server_extractor.py --channels CHANNEL_ID1 CHANNEL_ID2

# Limit number of messages per channel
python discord_server_extractor.py --max-messages 1000

# Specify custom output directory
python discord_server_extractor.py --output-dir my_extraction_folder

# Use command-line credentials instead of .env
python discord_server_extractor.py --token YOUR_TOKEN --server SERVER_ID
```

### Step 2: Analyze User

Perform comprehensive psychological analysis on a specific user's messages:

```bash
python discord_psycho_analyzer.py --user-id USER_ID
```

Replace `USER_ID` with the Discord user ID you want to analyze.

#### Interactive User Selection

If you don't specify a user ID, the tool will show you all available users:

```bash
python discord_psycho_analyzer.py
```

This will display a numbered list of users with message counts for easy selection.

#### Additional Analysis Options

```bash
# Analyze specific user file directly
python discord_psycho_analyzer.py --user-file path/to/username_userid.json

# Specify custom data directory
python discord_psycho_analyzer.py --data-dir my_extraction_folder

# Use custom output directory
python discord_psycho_analyzer.py --output-dir my_analysis_results

# Specify DeepSeek model
python discord_psycho_analyzer.py --model deepseek-chat --user-id USER_ID
```

### Step 3: View Results

The comprehensive analysis creates multiple output files:

```
psychological_analysis/
├── comprehensive_analysis_USERNAME_TIMESTAMP.json    # Complete analysis data
├── final_analysis_USERNAME_TIMESTAMP.txt           # Human-readable report  
├── metrics_report_USERNAME_TIMESTAMP.txt           # Detailed behavioral metrics
└── analysis_log_USERNAME_TIMESTAMP.txt             # Iteration progression log
```

Where `USERNAME` and `TIMESTAMP` are replaced with actual values.

**Analysis Features:**
- **Iterative Processing**: Messages are analyzed in chunks for comprehensive insights
- **Behavioral Metrics**: Temporal patterns, linguistic analysis, social dynamics
- **Big Five Personality Assessment**: Detailed scoring with reasoning
- **Mental Health Indicators**: Emotional patterns and risk assessment
- **Geographic Analysis**: Location estimation from communication patterns
- **Relationship Analysis**: Social connections and interaction styles

## Output

The tool generates comprehensive psychological analysis reports including:

### Final Analysis Report
- **Geographic Assessment**: Location estimation with confidence levels
- **Big Five Personality Profile**: Detailed scoring (1-10) with comprehensive reasoning
- **Sexuality & Relationship Analysis**: Orientation, attachment style, relationship patterns
- **Mental Health Assessment**: Emotional regulation, risk factors, support systems
- **Social Dynamics**: Communication style, relationship patterns, social hierarchy
- **Behavioral Insights**: Lifestyle patterns, decision-making style, cognitive indicators
- **Risk Assessment**: Mental health concerns and protective factors

### Detailed Metrics Report
- **Temporal Patterns**: Activity schedules, circadian preferences, consistency metrics
- **Linguistic Analysis**: Communication style, vocabulary patterns, emotional expression
- **Social Interaction Data**: Mention patterns, relationship networks, engagement scores
- **Emotional Indicators**: Sentiment analysis, volatility measures, mental health markers
- **Content Topics**: Interest areas and focus patterns
- **Personality Indicators**: Trait-specific behavioral markers

### Processing Features
- **Iterative Analysis**: Messages processed in chunks for comprehensive coverage
- **Multi-dimensional Assessment**: Combines behavioral metrics with AI analysis
- **Confidence Scoring**: Reliability ratings for different assessment areas
- **Longitudinal Insights**: Communication evolution over time

## File Structure

```
psychoshit/
├── discord_server_extractor.py      # Message extraction script
├── discord_psycho_analyzer.py       # Psychological analysis script
├── output/                           # Default extraction output
│   └── ServerName_ServerID_TIMESTAMP/
│       ├── complete_user_data.json
│       ├── individual_users/         # Individual user JSON files
│       ├── user_statistics.json
│       ├── user_summary.csv
│       └── README.md
├── psychological_analysis/          # Analysis output directory
│   ├── comprehensive_analysis_*.json    # Complete analysis data
│   ├── final_analysis_*.txt            # Human-readable reports
│   ├── metrics_report_*.txt            # Behavioral metrics
│   └── analysis_log_*.txt              # Processing logs
├── .env                            # Environment variables
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Troubleshooting

### Common Issues

**Authentication Error**: Ensure your Discord token is valid and properly formatted in the `.env` file.

**Server Access Error**: Verify that your Discord account has access to the specified server.

**API Rate Limits**: The tool includes rate limiting to respect Discord's API limits. Large servers may take time to process.

**Extraction Output**: The extractor saves data in timestamped folders under the `output/` directory by default. Use `--output-dir` to specify a different location.

**Channel Selection**: By default, all text channels are extracted. Use `--channels` parameter to extract specific channels only.

**Analysis Processing**: The psychological analyzer uses iterative processing, breaking large message sets into chunks for comprehensive analysis while respecting API limits.

**DeepSeek API Limits**: The tool automatically handles rate limiting and token limits for optimal processing.

**Missing Dependencies**: Run `pip install -r requirements.txt` to ensure all required packages are installed.

## Legal and Ethical Considerations

- Only analyze servers where you have explicit permission
- Respect user privacy and data protection laws
- Follow Discord's Terms of Service
- Use responsibly and ethically
- Consider informing users if their data is being analyzed

---

**Remember**: This tool should only be used with proper authorization and in compliance with all applicable laws and terms of service.
