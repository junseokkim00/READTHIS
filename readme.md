# `readthis`
A SAAS for recent paper recommendations based on AI conferences
![image](./assets/logo.png)


# Novelty
+ generate database based on academic paper links (citations and references)
+ advanced search for specific settings
    + fetching paper from Semantic Scholar Open research corpus
    + use web search?
    + rss feed search

## Services

### What's Next? 📄
+ find next paper based on the paper you are currently reading

### Daily Paper 📄
+ find relevant papers based on your collection of papers
+ connected with Zotero

### Paper Hunt 🕵️‍♂️
+ find the latest papers that sounds interesting in rss feed


## How to use `readthis`?

1. Prepare python libraries

- python3: 3.9.19
``` bash
$ conda create -n readthis python=3.9
$ conda activate readthis
$ conda install ipykernel
$ pip install -r requirements.txt
```




## TODO
- [X] Connect not only reference papers, but also citation papers for the given query
- [X] Zotero import
- [X] RSS Feed connection
- [ ] Web search functionality
- [X] Dataframe exportation

## References
[semantic scholar api example](https://github.com/allenai/s2-folks/tree/main/examples/python) : github link for using semantic scholar api

[multiple pages streamlit.io](https://docs.streamlit.io/get-started/tutorials/create-a-multipage-app): tutorial of streamlit making multi-pages

[arxiv dataset](https://www.kaggle.com/datasets/Cornell-University/arxiv?resource=download)

[structure-vision](https://github.com/lfoppiano/structure-vision/tree/main): structure pdf using vision

[Zotero-agent](https://vankhoa21991.medium.com/unleashing-the-power-of-ai-crafting-intelligent-insights-with-large-language-models-and-refined-dfc07c648619)

[searxng-docker](https://github.com/searxng/searxng-docker)

[langchain tool searxng search](https://python.langchain.com/docs/integrations/tools/searx_search/)

[scholarly for python](https://github.com/scholarly-python-package/scholarly?tab=readme-ov-file)

[S2ORC](https://github.com/allenai/s2orc)
