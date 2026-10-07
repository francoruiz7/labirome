# La Birome

**Automated news site: an LLM pipeline that finds stories covered by several outlets, writes an original article, fact-checks it against its sources, picks a freely licensed photo and publishes it. No server, no CMS, no manual steps.**

Live site: [labirome.com](https://labirome.com)

## Overview

La Birome is an Argentine general news site that runs on its own. Twice a day a scheduled job reads the RSS feeds of seven national outlets, detects the stories that at least two of them are covering, and writes its own article from that material. Each article is checked before it goes out, and every one lists its sources at the bottom.

The whole thing runs on GitHub Actions and GitHub Pages. Running cost is the LLM usage only, around one US cent per article.

## How it works

1. **Read** — pulls recent headlines from the RSS feeds of seven outlets.
2. **Cluster** — an LLM groups headlines about the same event, scores their relevance and keeps only stories covered by two or more outlets.
3. **Gather** — downloads the full text of each source article.
4. **Write** — the LLM writes an original article using only facts present in the sources, following a house style guide.
5. **Fact-check** — a second LLM pass compares every figure, date, name and quote against the sources and grades each issue as serious or minor.
6. **Correct** — serious issues trigger one automatic correction and a re-check. If they persist, the article is held back instead of published.
7. **Originality check** — detects 12-word sequences shared with any source (quoted statements excluded) and rewrites those passages.
8. **Photo** — looks for a freely licensed image on Wikipedia and Wikimedia Commons, from the most specific search to a section-level fallback, and stores author and license for the credit line.
9. **Publish** — saves the article as JSON, rebuilds the static site and deploys it.

If an article is discarded or held back, the run moves on to the next candidate story until it reaches its quota.

## Features

- Fully unattended publishing on a schedule, with a manual trigger for on-demand runs
- Multi-source requirement: no story is written from a single outlet
- Two-stage quality control (fact-check with severity grading, originality check) with automatic correction
- Held-back articles kept in a separate folder for manual review
- Photos with free licenses only, always credited; no AI-generated images
- Static site generator written from scratch: home, section pages, article pages, client-side search, trending block, headline ticker
- Responsive design with a custom theme
- Every article discloses that it was produced with AI and links to its sources

## Tech stack

- **Python** — pipeline (`generar.py`) and static site generator (`construir.py`)
- **OpenAI API** — clustering, writing, fact-checking and rewriting, with JSON-structured outputs
- **feedparser / trafilatura** — RSS reading and article text extraction
- **Wikipedia and Wikimedia Commons APIs** — image search and license metadata
- **GitHub Actions** — scheduling, generation and deployment
- **GitHub Pages** — hosting, with a custom domain
- **HTML, CSS, vanilla JavaScript** — front end, no frameworks

## Structure

```
generar.py        Pipeline: read, cluster, write, check, find photo, save
construir.py      Static site generator
config.py         Sources, sections, quotas and quality-control switches
guia_estilo.md    House style guide given to the writer model
estatico/         CSS, JavaScript, logo and icons
notas/            Published articles (JSON)
retenidas/        Articles held back by the fact-check
.github/workflows/publicar.yml   Scheduled workflow
```

## Configuration

The API key is read from the `OPENAI_API_KEY` repository secret and is never stored in the code. Article quota, minimum number of sources, time window and the quality-control switches are set in `config.py`.

## Note

This is a personal project built to explore unattended LLM pipelines with quality controls. Articles are generated automatically and are not reviewed by a human editor before publication.
