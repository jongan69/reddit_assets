#!/usr/bin/env python3
"""
Test script for GitHub workflow dispatch API
Use this to debug Siri Shortcut issues
"""

import requests
import json
import os
from typing import Dict, Any

def test_workflow_dispatch(
    token: str,
    owner: str,
    repo: str,
    workflow_file: str = "reddit_post.yml",
    ref: str = "main",
    inputs: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Test GitHub workflow dispatch API
    
    Args:
        token: GitHub personal access token
        owner: Repository owner (username or org)
        repo: Repository name
        workflow_file: Workflow file name (default: reddit_post.yml)
        ref: Branch reference (default: main)
        inputs: Workflow input parameters
    
    Returns:
        Dict with status code and response details
    """
    
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_file}/dispatches"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "ref": ref
    }
    
    if inputs:
        payload["inputs"] = inputs
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        result = {
            "status_code": response.status_code,
            "success": response.status_code == 204,
            "headers": dict(response.headers),
            "url": url
        }
        
        if response.status_code != 204:
            try:
                result["error"] = response.json()
            except:
                result["error"] = response.text
        
        return result
        
    except Exception as e:
        return {
            "status_code": None,
            "success": False,
            "error": str(e),
            "url": url
        }

def main():
    """Interactive test function"""
    
    print("GitHub Workflow Dispatch Test")
    print("=" * 40)
    
    # Get credentials
    token = input("Enter your GitHub token: ").strip()
    owner = input("Enter repository owner (username/org): ").strip()
    repo = input("Enter repository name: ").strip()
    
    print("\nTesting basic workflow dispatch...")
    
    # Test 1: Basic dispatch (no inputs)
    result1 = test_workflow_dispatch(token, owner, repo)
    print(f"Basic test: {'✅ SUCCESS' if result1['success'] else '❌ FAILED'}")
    print(f"Status: {result1['status_code']}")
    if not result1['success'] and 'error' in result1:
        print(f"Error: {result1['error']}")
    
    print("\nTesting with inputs...")
    
    # Test 2: With inputs
    inputs = {
        "run_crypto_analysis": "true",
        "run_penny_stock_screener": "true",
        "debug_mode": "false"
    }
    
    result2 = test_workflow_dispatch(token, owner, repo, inputs=inputs)
    print(f"With inputs test: {'✅ SUCCESS' if result2['success'] else '❌ FAILED'}")
    print(f"Status: {result2['status_code']}")
    if not result2['success'] and 'error' in result2:
        print(f"Error: {result2['error']}")
    
    print("\n" + "=" * 40)
    
    if result1['success'] and result2['success']:
        print("🎉 All tests passed! Your setup should work with Siri Shortcuts.")
        print("\nUse this JSON in Siri Shortcuts:")
        print(json.dumps({
            "ref": "main",
            "inputs": inputs
        }, indent=2))
    else:
        print("❌ Some tests failed. Check the errors above.")
        print("\nCommon issues:")
        print("- GitHub token permissions (needs 'repo' scope)")
        print("- Repository name or owner incorrect")
        print("- Workflow file doesn't exist")
        print("- Input parameter names don't match workflow file")

if __name__ == "__main__":
    main() 