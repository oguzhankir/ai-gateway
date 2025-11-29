# Security Notice

## API Key Management

**IMPORTANT**: This repository does NOT contain any real API keys. All sensitive credentials are stored in `.env` files which are gitignored.

### Environment Variables

All API keys and secrets must be provided via environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key
- `GEMINI_API_KEY`: Your Google Gemini API key
- `ADMIN_API_KEY`: Admin API key for dashboard access
- `SECRET_KEY`: Secret key for cryptographic operations

### Default Values

Some files contain default/placeholder values for local development:
- `test_providers.sh`: Uses `dev-key-change-in-production` as default
- `frontend/src/lib/api.ts`: Uses fallback for development only
- `docker-compose.yml`: Uses environment variable substitution

**These defaults are NOT valid keys and will NOT work in production.**

### Before Deploying

1. Ensure `.env` file exists with real credentials
2. Never commit `.env` files to version control
3. Use environment-specific secret management in production
4. Rotate keys regularly
5. Use least-privilege access principles

### Verification

To verify no real keys are in the repository:

```bash
# Check for common API key patterns
grep -r "sk-proj\|AIzaSy" --exclude-dir=node_modules --exclude="*.md" --exclude="*.log" .

# Should only show .env files (which are gitignored)
```

