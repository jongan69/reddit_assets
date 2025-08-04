# Siri Shortcut GitHub Workflow Dispatch Guide

## Problem
Siri Shortcuts have issues with GitHub's workflow dispatch API, particularly with input parameters and JSON formatting.

## Solution

### 1. Basic Setup in Siri Shortcuts

1. **Add "Get Contents of URL" action**
2. **Configure the URL**: `https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/actions/workflows/reddit_post.yml/dispatches`
3. **Set Method**: POST
4. **Add Headers**:
   - `Authorization`: `token YOUR_GITHUB_TOKEN`
   - `Accept`: `application/vnd.github.v3+json`
   - `Content-Type`: `application/json`

### 2. Request Body Format

**IMPORTANT**: Don't use the Dictionary action. Instead, manually type the JSON in the "Request Body" field:

```json
{
  "ref": "main",
  "inputs": {
    "run_crypto_analysis": "true",
    "run_penny_stock_screener": "true",
    "debug_mode": "false"
  }
}
```

### 3. Key Points for Success

1. **Boolean Values**: Must be strings in quotes (`"true"`, `"false"`)
2. **Branch Reference**: Always include `"ref": "main"` (or your default branch)
3. **Input Names**: Must exactly match the input names in your workflow file
4. **GitHub Token**: Must have `repo` scope permissions

### 4. Debugging Steps

#### Step 1: Test with Minimal Inputs
Start with no inputs to verify basic connectivity:

```json
{
  "ref": "main"
}
```

#### Step 2: Add Inputs One by One
Add inputs individually to identify which one causes issues:

```json
{
  "ref": "main",
  "inputs": {
    "run_crypto_analysis": "true"
  }
}
```

#### Step 3: Check GitHub Token Permissions
Ensure your token has these scopes:
- `repo` (full repository access)
- `workflow` (if using fine-grained tokens)

#### Step 4: Verify Workflow File
Make sure your workflow file is in the correct location:
`.github/workflows/reddit_post.yml`

### 5. Alternative: Use GitHub CLI

If Siri Shortcuts continue to fail, consider using GitHub CLI in a script:

```bash
gh workflow run reddit_post.yml --ref main --field run_crypto_analysis=true --field run_penny_stock_screener=true --field debug_mode=false
```

### 6. Testing the API Directly

Test your API call using curl to verify it works:

```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Content-Type: application/json" \
  https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/actions/workflows/reddit_post.yml/dispatches \
  -d '{
    "ref": "main",
    "inputs": {
      "run_crypto_analysis": "true",
      "run_penny_stock_screener": "true",
      "debug_mode": "false"
    }
  }'
```

### 7. Common Error Codes

- **401**: Unauthorized - Check your GitHub token
- **403**: Forbidden - Token lacks required permissions
- **404**: Not found - Check repository name or workflow file path
- **422**: Validation failed - Check input parameter names and types

### 8. Siri Shortcut Variables

If you want to make inputs dynamic, use Siri Shortcut variables in the JSON:

```json
{
  "ref": "main",
  "inputs": {
    "run_crypto_analysis": "true",
    "run_penny_stock_screener": "true",
    "debug_mode": "ShortcutInput"
  }
}
```

Where `ShortcutInput` is a variable you can set before the API call.

## Troubleshooting Checklist

- [ ] GitHub token has `repo` scope
- [ ] Workflow file exists at `.github/workflows/reddit_post.yml`
- [ ] Input parameter names match exactly (case-sensitive)
- [ ] Boolean values are strings: `"true"` not `true`
- [ ] JSON is properly formatted (no extra commas)
- [ ] Repository name is correct
- [ ] Branch name is correct

## Success Indicators

When successful, you should:
1. Get a 204 status code (no content)
2. See a new workflow run appear in your GitHub Actions tab
3. No error messages in Siri Shortcuts 