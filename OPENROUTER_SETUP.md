# 🤖 OpenRouter Integration Setup Guide

This guide will help you set up OpenRouter integration with your Open WebUI instance, enabling access to multiple AI models including Perplexity Sonar for web search capabilities.

## 🎯 What is OpenRouter?

OpenRouter is a unified API that provides access to multiple AI models from different providers through a single interface. This includes:

- **Perplexity Sonar models** for real-time web search
- **Claude models** from Anthropic
- **GPT models** from OpenAI
- **Open-source models** like Llama, Mistral, and more
- **Cost optimization** through intelligent routing

## 🚀 Quick Setup

### Option 1: Interactive Setup (Recommended)

Run the interactive configuration manager:

```bash
python3 manage_openrouter.py
```

This will launch a colorful, user-friendly interface with menu navigation to:
- ✅ Configure your OpenRouter API key
- 🧪 Test the connection
- 🔍 Browse available models
- 🐳 Restart Docker services
- 📊 View current configuration

### Option 2: Manual Setup

1. **Get your OpenRouter API key**
   - Visit [https://openrouter.ai/keys](https://openrouter.ai/keys)
   - Create an account and generate an API key

2. **Create/update your .env file**
   ```bash
   cp env.example .env
   # Edit .env and add your API key
   ```

3. **Configure environment variables**
   ```bash
   ENABLE_OPENROUTER_API=true
   OPENROUTER_API_KEY=your_actual_api_key_here
   OPENROUTER_API_BASE_URL=https://openrouter.ai/api/v1
   ```

4. **Restart Docker services**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## 🔍 Adding OpenRouter Models in Open WebUI

**Important:** OpenRouter models are added as **Direct Connections** in Open WebUI, not automatically loaded. This is by design for performance and cost control.

### Step-by-Step Process:

1. **Open Open WebUI** in your browser (`http://localhost`)

2. **Access Model Management:**
   - Click on your profile/settings
   - Go to **Admin Panel** → **Settings** → **Connections**
   - Or look for **"Manage Direct Connections"**

3. **Add OpenRouter Connection:**
   - Click **"+"** to add a new connection
   - **URL:** `https://openrouter.ai/api/v1`
   - **API Key:** Your OpenRouter API key
   - **Name:** Give it a descriptive name (e.g., "Perplexity Sonar Pro")

4. **Test the Connection:**
   - Click the test button to verify it works
   - You should see "success" ✅

5. **The model is now available** in your model selector dropdown!

### Popular OpenRouter Models to Add:

**For Web Search:**
- `perplexity/llama-3.1-sonar-large-128k-online`
- `perplexity/llama-3.1-sonar-huge-128k-online`
- `perplexity/llama-3.1-sonar-small-128k-online`

**For General Use:**
- `anthropic/claude-3.5-sonnet`
- `openai/gpt-4o`
- `meta-llama/llama-3.1-405b-instruct`

## 🔍 Using Perplexity for Web Search

Once you've added a Perplexity Sonar model:

### Example Usage:
1. Select the Perplexity Sonar model in Open WebUI
2. Ask questions that require current information:
   - "What are the latest developments in AI this week?"
   - "Current stock price of NVIDIA"
   - "Recent news about climate change"

The model will automatically search the web and provide up-to-date information with sources.

## 🛠️ Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_OPENROUTER_API` | `true` | Enable/disable OpenRouter integration |
| `OPENROUTER_API_KEY` | - | Your OpenRouter API key |
| `OPENROUTER_API_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter API endpoint |

### Docker Compose Integration

The OpenRouter configuration is automatically included in your `docker-compose.yaml`:

```yaml
environment:
  - ENABLE_OPENROUTER_API=${ENABLE_OPENROUTER_API:-true}
  - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
  - OPENROUTER_API_BASE_URL=${OPENROUTER_API_BASE_URL:-https://openrouter.ai/api/v1}
```

## 🧪 Testing Your Setup

### Using the Management Script
```bash
python3 manage_openrouter.py
# Navigate to "Test OpenRouter Connection"
```

### Manual Testing
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://openrouter.ai/api/v1/models
```

## 🎨 Management Script Features

The `manage_openrouter.py` script provides:

- **🎮 Menu Navigation** - User-friendly interface
- **🔧 Easy Configuration** - Step-by-step setup
- **🧪 Connection Testing** - Verify your setup works
- **🔍 Model Browser** - See available models
- **🐳 Docker Integration** - Restart services easily
- **📊 Status Dashboard** - View current configuration
- **❓ Built-in Help** - Documentation and tips

## 🔒 Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive data
3. **Rotate API keys** regularly
4. **Monitor usage** on OpenRouter dashboard
5. **Set spending limits** if available

## 🐛 Troubleshooting

### Common Issues

**❌ "Models not appearing automatically"**
- **This is normal!** OpenRouter models must be added manually as Direct Connections
- Follow the "Adding OpenRouter Models" section above

**❌ "Connection failed: HTTP 401"**
- Solution: Check your API key is correct and active

**❌ "CORS errors"**
- Solution: This is normal for Direct Connections, the models should still work

**❌ "Permission denied on script"**
- Solution: `chmod +x manage_openrouter.py`

### Debug Steps

1. **Check configuration**
   ```bash
   python3 manage_openrouter.py
   # Select "View Current Configuration"
   ```

2. **Test connection**
   ```bash
   python3 manage_openrouter.py
   # Select "Test OpenRouter Connection"
   ```

3. **Check Docker logs**
   ```bash
   docker-compose logs open-webui
   ```

4. **Verify environment variables**
   ```bash
   docker-compose config
   ```

## 🔗 Useful Links

- **OpenRouter Dashboard**: [https://openrouter.ai/](https://openrouter.ai/)
- **API Documentation**: [https://openrouter.ai/docs](https://openrouter.ai/docs)
- **Model Pricing**: [https://openrouter.ai/models](https://openrouter.ai/models)
- **Open WebUI Docs**: [https://docs.openwebui.com/](https://docs.openwebui.com/)

## 💡 Pro Tips

1. **Add models one by one** to control costs and performance
2. **Use Perplexity Sonar** for questions requiring current information
3. **Monitor your usage** to avoid unexpected costs
4. **Give models descriptive names** when adding them as Direct Connections
5. **Test each model** after adding to ensure it works correctly

## 🆘 Getting Help

If you encounter issues:

1. **Check this guide** for common solutions
2. **Run the management script** for interactive troubleshooting
3. **Check Docker logs** for error messages
4. **Verify your API key** on the OpenRouter dashboard

---

**Happy AI chatting with OpenRouter! 🚀** 