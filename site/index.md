<div class="hero" markdown="1">

# The Self-Hosting & Home Lab Guide

<p class="lead">A comprehensive, opinionated, in-depth guide to the services worth running on your own hardware — and everything you need around them: hardware, networking, storage, containers, reverse proxies, remote access, identity, backups, monitoring, security, and operations.</p>

<div class="pill-row">
<a class="pill" href="00-introduction/">Start here</a>
<a class="pill" href="31-reference-architectures/">Reference architectures</a>
<a class="pill" href="15-media/">Media</a>
<a class="pill" href="11-backups/">Backups</a>
<a class="pill" href="08-remote-access-vpn/">Remote access</a>
<a class="pill" href="23-ai-llm/">Local AI</a>
</div>

</div>

**{{CHAPTER_COUNT}} chapters, ~{{WORD_COUNT}} words.** Each chapter is also available as plain Markdown in the [repository](https://github.com/gorg667/self-host-guide), and the whole guide is concatenated into a single [`SELF-HOSTING-GUIDE.md`](https://github.com/gorg667/self-host-guide/blob/main/SELF-HOSTING-GUIDE.md) file.

**How to read it.** Newcomers: read Part I in order, then Part II — those cover the infrastructure that every application sits on. Experienced admins: jump straight to the service reviews in Part III, then pick up the operational material in Part IV. Every service review states what it is, why you would choose it, what to watch out for, rough resource needs, a minimal `docker-compose.yml`, and alternatives.

**Conventions.** Opinions are labelled as such. Resource figures are for typical small household usage. Compose snippets are minimal and intentionally omit things (reverse-proxy labels, networks, secrets management) that the infrastructure chapters cover in depth. "As of 2026" marks claims that will age.
