"""Static list of GitHub trivia shown by the `/api/facts` endpoint.

Kept as plain config (not a database table) since the list is small, static,
and doesn't need to be queried or mutated at runtime.
"""

GITHUB_FACTS: list[str] = [
    "GitHub was founded in 2008 by Tom Preston-Werner, Chris Wanstrath, PJ Hyett, and Scott Chacon.",
    "The name 'GitHub' combines Git, the version control system created by Linus Torvalds, with 'Hub' as a central meeting point.",
    "Microsoft acquired GitHub in 2018 for approximately 7.5 billion dollars.",
    "GitHub's mascot is an anthropomorphized octopus-cat hybrid named Octocat.",
    "The Linux kernel repository is one of the largest and most active open-source projects hosted on GitHub.",
    "GitHub introduced Actions, its built-in CI/CD platform, in 2019.",
    "GitHub Pages lets anyone host a static website for free directly from a repository.",
    "The 'git' command name was chosen by Linus Torvalds, who joked it means 'unpleasant person' in British slang.",
    "GitHub Copilot, an AI pair programmer, was launched in 2021 in partnership with OpenAI.",
    "As of the mid-2020s, GitHub hosts well over 400 million repositories.",
    "The first commit to the Git source code itself was made by Linus Torvalds in April 2005.",
    "GitHub's Octoverse report is an annual review of trends across the platform's open-source ecosystem.",
    "Repositories can be 'starred' to bookmark them, and stars are commonly used as an informal popularity signal.",
    "GitHub supports 'topics', which let maintainers tag repositories with subject labels like 'machine-learning' or 'react'.",
    "The largest single file GitHub will render in a browser is capped for performance; huge files must be downloaded instead.",
    "GitHub Sponsors, launched in 2019, lets developers get paid directly for their open-source work.",
    "A GitHub organization can own repositories collectively, separate from any single user account.",
    "GitHub's search supports a rich qualifier syntax like 'language:', 'stars:', and 'topic:' for precise queries.",
    "The 'fork' feature, copying someone else's repository into your own account, predates GitHub but was popularized by it.",
    "GitHub Codespaces provides a full cloud development environment that spins up directly from a repository.",
    "Git itself is a distributed version control system, meaning every clone is a full copy of the project's history.",
    "The octocat mascot has appeared in dozens of playful variants for holidays and special events over the years.",
    "GitHub's GraphQL API, launched in 2016, lets clients request exactly the fields they need in a single round trip.",
    "Dependabot, now part of GitHub, automatically opens pull requests to update vulnerable or outdated dependencies.",
]
