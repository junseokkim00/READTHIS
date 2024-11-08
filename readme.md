# `readthis`
A SAAS for recent paper recommendations based on AI conferences


# Novelty
+ advanced search for specific settings
    + specific conference
    + paper type (short/long)
    + findings, main, workshop (seperated)
    + more?

## How it works

TBA


## Ablations

- [ ] What if we use both original query, and rewritten query for retrieval?
- [ ] ETC

## How to use `readthis`?

1. Prepare python libraries

- python3: 3.9.19
``` bash
$ conda create -n readthis python=3.9
$ conda activate readthis
$ conda install ipykernel
$ pip install -r requirements.txt
```


+ semantic scholar api로 reference 가져오기
  + citations 가져오기



### Architecture
- `readthis.py`
- `pages`
  - `1_`



## TODO
- [X] Connect not only reference papers, but also citation papers for the given query
- [ ] Implement KNN for un-cited papers + citations
- [ ] Zotero import export

## References
[semantic scholar api example](https://github.com/allenai/s2-folks/tree/main/examples/python) : github link for using semantic scholar api

[multiple pages streamlit.io](https://docs.streamlit.io/get-started/tutorials/create-a-multipage-app): tutorial of streamlit making multi-pages

[arxiv dataset](https://www.kaggle.com/datasets/Cornell-University/arxiv?resource=download)

[structure-vision](https://github.com/lfoppiano/structure-vision/tree/main): structure pdf using vision

[Zotero-agent](https://vankhoa21991.medium.com/unleashing-the-power-of-ai-crafting-intelligent-insights-with-large-language-models-and-refined-dfc07c648619)

[searxng-docker](https://github.com/searxng/searxng-docker)

[langchain tool searxng search](https://python.langchain.com/docs/integrations/tools/searx_search/)

[scholarly for python](https://github.com/scholarly-python-package/scholarly?tab=readme-ov-file)

<details>
<summary>Click to toggle contents of `code`</summary>

```
CODE!
```
</details>