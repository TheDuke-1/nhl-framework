# SUPERHUMAN FRAMEWORK V2 — SETUP GUIDE

> **What This Is:** Step-by-step instructions for installing the Superhuman Framework. Written for someone who's smart but not technical.

> **Time Required:** About 30-45 minutes for full setup

---

## OVERVIEW: What We're Installing

The framework has three parts:

1. **Global Files** → Rules and commands that work across ALL your projects
2. **Project Files** → Rules, commands, and agents for a specific project
3. **GitHub Template** → A starting point for new projects that inherits all learnings

---

## BEFORE YOU START

### You'll Need:
- [ ] Claude Code installed and working
- [ ] Terminal access (Claude Code uses this)
- [ ] A GitHub account
- [ ] The framework zip file downloaded

### Don't Have Claude Code Yet?
1. Go to claude.ai
2. Download the Claude Code CLI
3. Follow their installation instructions
4. Come back here when `claude` command works in terminal

---

## PHASE 1: Install Global Files

**What This Does:** Sets up commands that work in any project (like `/interview`, `/session-start`)

**Where Files Go:** `~/.claude/` (a hidden folder in your home directory)

### Step 1.1: Open Terminal

On Mac:
- Press `Cmd + Space`
- Type "Terminal"
- Press Enter

### Step 1.2: Create the Global Folder

Copy and paste this command, then press Enter:

```bash
mkdir -p ~/.claude/commands
```

**What this does:** Creates the folder structure Claude Code needs.

### Step 1.3: Extract Framework Files

If you downloaded the zip file, extract it somewhere you can find it (like Downloads or Desktop).

### Step 1.4: Copy Global Files

Replace `[PATH]` with where you extracted the files:

```bash
cp [PATH]/superhuman-framework-v2/global/CLAUDE.md ~/.claude/
cp [PATH]/superhuman-framework-v2/global/commands/*.md ~/.claude/commands/
```

**Example if extracted to Downloads:**
```bash
cp ~/Downloads/superhuman-framework-v2/global/CLAUDE.md ~/.claude/
cp ~/Downloads/superhuman-framework-v2/global/commands/*.md ~/.claude/commands/
```

### Step 1.5: Verify Installation

```bash
ls ~/.claude/
```

**You should see:**
```
CLAUDE.md    commands
```

```bash
ls ~/.claude/commands/
```

**You should see:**
```
design-audit.md       framework-improve.md  session-end.md
design-interview.md   interview.md          session-start.md
quick-fix.md
```

### ✅ Phase 1 Complete!

Global commands are now available in all projects.

---

## PHASE 2: Set Up Your First Project

Choose ONE:
- **Phase 2A:** If you have an EXISTING project (like Links Ledger)
- **Phase 2B:** If you're starting a NEW project

---

## PHASE 2A: Add Framework to Existing Project

**What This Does:** Adds the framework to a project you've already been building

### Step 2A.1: Navigate to Your Project

```bash
cd ~/path/to/your/project
```

**Example for Links Ledger:**
```bash
cd ~/Developer/LinksLedger
```

### Step 2A.2: Create Safety Backup

Before changing anything, let's make a backup:

```bash
git checkout -b pre-framework-backup
git add -A
git commit -m "Backup before framework installation"
git checkout main
```

**What this does:** Creates a save point you can return to if anything goes wrong.

### Step 2A.3: Backup Existing CLAUDE.md (If You Have One)

```bash
cp CLAUDE.md CLAUDE.md.backup 2>/dev/null || echo "No existing CLAUDE.md"
```

### Step 2A.4: Create Project Folders

```bash
mkdir -p .claude/commands .claude/agents
```

### Step 2A.5: Copy Project Files

Replace `[PATH]` with where you extracted the framework:

```bash
cp [PATH]/superhuman-framework-v2/template/.claude/commands/*.md .claude/commands/
cp [PATH]/superhuman-framework-v2/template/.claude/agents/*.md .claude/agents/
cp [PATH]/superhuman-framework-v2/template/.claude/settings.json .claude/
cp [PATH]/superhuman-framework-v2/template/.mcp.json .
```

### Step 2A.6: Copy Template Files to Project Root

```bash
cp [PATH]/superhuman-framework-v2/template/DESIGN-SYSTEM.md .
cp [PATH]/superhuman-framework-v2/template/DESIGN-DECISIONS.md .
cp [PATH]/superhuman-framework-v2/template/LEARNINGS.md .
cp [PATH]/superhuman-framework-v2/template/SESSION-STATE.md .
```

### Step 2A.7: For SwiftUI/iOS Projects — Add Swift-Specific Files

If your project is a SwiftUI app (like Links Ledger):

```bash
cp [PATH]/superhuman-framework-v2/swiftui/.claude/commands/*.md .claude/commands/
cp [PATH]/superhuman-framework-v2/swiftui/.claude/agents/*.md .claude/agents/
```

### Step 2A.8: Merge CLAUDE.md Files

**IMPORTANT:** Don't replace your existing CLAUDE.md — merge them.

1. Open Claude Code in your project:
   ```bash
   claude
   ```

2. Give Claude this prompt:
   ```
   I need to merge my existing CLAUDE.md with the new framework CLAUDE.md.
   
   My existing file: CLAUDE.md.backup
   New framework template: [PATH]/superhuman-framework-v2/template/CLAUDE.md
   SwiftUI additions: [PATH]/superhuman-framework-v2/swiftui/CLAUDE.md
   
   Please:
   1. Read both files
   2. Combine them intelligently (keep my project-specific rules, add framework structure)
   3. Show me the merged result
   4. Save it as CLAUDE.md
   ```

### Step 2A.9: Verify Everything Works

```bash
# Check Xcode still builds (for iOS projects)
# Open in Xcode and press Cmd+B

# Check commands are available
ls .claude/commands/
ls .claude/agents/
```

### Step 2A.10: Run Design Audit

Now that the framework is installed, run the design audit:

1. Open Claude Code in your project: `claude`
2. Type: `/design-audit`
3. Claude will walk through your existing views with you

### ✅ Phase 2A Complete!

Your existing project now has the full framework.

---

## PHASE 2B: Start a New Project

**What This Does:** Creates a new project with the framework already set up

### Step 2B.1: Use GitHub Template (If Set Up)

If you've completed Phase 3 (GitHub Template), you can create new projects from your template:

1. Go to your template repository on GitHub
2. Click "Use this template" → "Create a new repository"
3. Name your project
4. Clone it locally

### Step 2B.2: Manual Setup (If No Template Yet)

```bash
# Create project folder
mkdir ~/Developer/MyNewProject
cd ~/Developer/MyNewProject

# Initialize git
git init

# Copy all template files
cp -r [PATH]/superhuman-framework-v2/template/. .

# For SwiftUI projects, add Swift files
cp [PATH]/superhuman-framework-v2/swiftui/.claude/commands/*.md .claude/commands/
cp [PATH]/superhuman-framework-v2/swiftui/.claude/agents/*.md .claude/agents/
```

### Step 2B.3: Customize CLAUDE.md

Open `CLAUDE.md` and fill in the project-specific sections:
- Project name and description
- Technology stack
- Design system (will be filled by `/design-interview`)

### Step 2B.4: Run Design Interview

1. Open Claude Code: `claude`
2. Type: `/design-interview`
3. Answer questions about your visual identity
4. Claude creates your DESIGN-SYSTEM.md

### ✅ Phase 2B Complete!

Your new project is ready with the full framework.

---

## PHASE 3: Create GitHub Template

**What This Does:** Makes a template repository so every new project starts with your learnings

**Why It Matters:** As your framework learns, new projects should inherit that knowledge

### Step 3.1: Create Template Repository

```bash
# Create a new folder for the template
mkdir ~/Developer/superhuman-template
cd ~/Developer/superhuman-template

# Initialize git
git init

# Copy template files
cp -r [PATH]/superhuman-framework-v2/template/. .
```

### Step 3.2: Customize for Your Defaults

Edit CLAUDE.md to include your universal preferences (things that apply to all your projects).

### Step 3.3: Push to GitHub

```bash
git add -A
git commit -m "Initial superhuman template"
gh repo create superhuman-template --public --source=. --push
```

### Step 3.4: Mark as Template

```bash
gh api repos/YOUR-GITHUB-USERNAME/superhuman-template --method PATCH -f is_template=true
```

Replace `YOUR-GITHUB-USERNAME` with your actual GitHub username.

### Step 3.5: Verify

Go to github.com/YOUR-USERNAME/superhuman-template and verify you see "Use this template" button.

### ✅ Phase 3 Complete!

You can now create new projects from your template.

---

## PHASE 4: Xcode 26.3 Integration (iOS Projects)

**What This Does:** Connects Claude to Xcode's new AI features for visual preview testing

### Step 4.1: Update Xcode

1. Open App Store
2. Check for Xcode updates
3. Update to 26.3 or later

### Step 4.2: Enable Claude Agent in Xcode

1. Open Xcode
2. Go to Settings (Cmd + ,)
3. Click "Agents" tab
4. Click "Install" next to Claude Agent
5. Sign in with your Anthropic account

### Step 4.3: Install XcodeBuildMCP

In terminal:
```bash
npm install -g xcodebuildmcp@beta
```

### Step 4.4: Configure MCP

The framework includes a `.mcp.json` file. Make sure it's in your project root.

Edit it to point to your project's .xcodeproj file:

```json
{
  "mcpServers": {
    "xcodebuild": {
      "command": "xcodebuildmcp",
      "args": ["--project", "./YourProject.xcodeproj"]
    }
  }
}
```

### Step 4.5: Verify Integration

1. Open Claude Code in your project: `claude`
2. Type: `/project:visual-verify`
3. Claude should capture Xcode previews and analyze them

### ✅ Phase 4 Complete!

Visual testing with Xcode previews is now available.

---

## PHASE 5: Verify Everything Works

### Test Global Commands

```bash
cd ~/Developer/YourProject
claude
```

In Claude Code, try:
- `/session-start` → Should load or create session state
- `/interview I want to build a simple test feature` → Should start asking questions
- Press Ctrl+C to exit the interview

### Test Project Commands

In Claude Code:
- `/project:status` → Should show project state
- `/project:verify` → Should run verification pipeline

### Test Agents

In Claude Code:
- `/agent:code-reviewer` → Should activate Code Reviewer agent

### ✅ All Phases Complete!

Your Superhuman Framework is fully installed.

---

## TROUBLESHOOTING

### "Command not found" for global commands

**Problem:** `/interview` doesn't work

**Solution:** Check global files are installed:
```bash
ls ~/.claude/commands/
```

If empty, repeat Phase 1.

---

### "Command not found" for project commands

**Problem:** `/project:build` doesn't work

**Solution:** Check project files are installed:
```bash
ls .claude/commands/
```

If empty, repeat Phase 2.

---

### Xcode previews not capturing

**Problem:** `/project:visual-verify` can't see previews

**Solutions:**
1. Make sure Xcode is open with your project
2. Make sure previews are visible (canvas showing)
3. Check XcodeBuildMCP is installed: `which xcodebuildmcp`
4. Check .mcp.json points to correct .xcodeproj

---

### Git errors

**Problem:** Git commands fail

**Solution:** Make sure you're in a git repository:
```bash
git status
```

If not initialized:
```bash
git init
```

---

### Claude seems to ignore CLAUDE.md

**Problem:** Claude doesn't follow rules in CLAUDE.md

**Solutions:**
1. Start a fresh Claude Code session
2. Make sure CLAUDE.md is in the project root
3. Check for syntax errors in CLAUDE.md

---

## WHAT'S NEXT?

1. **Run `/design-audit`** (existing projects) or **`/design-interview`** (new projects)
2. **Read `QUICK-START.md`** for daily reference
3. **Read `MASTER-GUIDE.md`** for complete understanding
4. **Start building!**

---

## GETTING HELP

If you get stuck:
1. Check this troubleshooting section
2. Ask Claude: "I'm having trouble with [X], can you help?"
3. Run `/framework-improve` and describe the issue — it may suggest a fix

---

*Setup complete. Time to build something superhuman.*
