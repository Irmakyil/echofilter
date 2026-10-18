# Data sources

## Public reference corpus

`disaster_response_training.csv` is the training split from Robert Munro's **Disaster Response Messages** dataset. It contains historical, human-labeled disaster messages from Haiti, Pakistan, Hurricane Sandy, and news sources. The dataset description reports that sensitive messages were removed and that the public release contains no records labeled as containing PII. This is a privacy-screened public dataset, not a guarantee that every free-text record is risk-free; review before republishing or processing.

Attribution: Robert Munro. 2012. *Processing short message communications in low-resource languages*. PhD dissertation, Stanford University. Dataset repository: https://github.com/rmunro/disaster_response_messages. License: Creative Commons Attribution 4.0 International (CC BY 4.0): https://creativecommons.org/licenses/by/4.0/.

Do not combine the corpus with other data to identify people. The messages are historical and do not include the retweet counts or normalized location fields needed for live triage. Use it only to inspect the labeled reference sample, not to direct aid.

## 2023 Türkiye earthquake benchmark

`depremkit_gold_anonymized.csv` is a privacy-preserving, label-only derivative of DepremKit's 3,750-row human-labeled Gold dataset. DepremKit is directly relevant to earthquake help-call classification and address/person entity recognition. This derived file removes tweet IDs, original ordering, source text, and raw entity spans; it retains translated message classes, the binary rescue label, and per-record entity-tag counts. It can show label distributions and schema coverage, but it cannot be used to run or reproduce text classification or NER because tweet text is not included.

Source: Çağrı Toraman, İzzet Emre Küçükkaya, Oğuzhan Özçelik, and Ümitcan Şahin (2023), *Tweets Under the Rubble: Detection of Messages Calling for Help in Earthquake Disaster*, https://arxiv.org/abs/2302.13403; dataset repository: https://github.com/DepremKit/depremkit. The upstream repository declares the MIT License; a copy is provided in `DEPREMKIT_LICENSE.txt`. This anonymized derivative is provided with source attribution and license context. It is not a real-time feed and must not be used to infer identities or locate survivors.

## Synthetic demo

`synthetic_incidents.csv` is generated for this project. It contains fictional names, locations, posts, and engagement counts. It is designed to demonstrate duplicates, low-visibility urgent cases, incomplete reports, and noise. It is not derived from identifiable disaster posts.
