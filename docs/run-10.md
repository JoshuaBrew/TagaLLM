# TagaLLM Run 10

TagaLLM is a local assistant for Philippine reference questions and everyday Tagalog and Taglish conversation. We started with unadapted Google Gemma 4 E2B IT, which answered directly on 73.0% of the factual prompts, often fell back to source notes, and lost track of the pickup time in a chair-rental roleplay. Run 9 brought direct answers to 86.5% and showed gains in note synthesis and dialogue state. Run 10 continued training the Run 9 adapter to sharpen factual completeness, alongside changes to the app's retrieval and factual checks.

## Stage 1 — Base Gemma vs. Run 9 (Establishing Grounding & Memory)

The overnight Run 9 evaluation replayed the same 37 information prompts and 21 conversation turns against the saved unadapted Google Gemma 4 E2B IT control. Both used the same frozen source snapshot. Run 9 answered directly on 32 of 37 information prompts, up from 27 of 37 for base Gemma. Source-note fallbacks fell from eight to three. Each model also returned one clarification and one no-source reply.

| Overnight measure | Base Gemma | Run 9 |
| :--- | :--- | :--- |
| Direct generated answers | 73.0% | 86.5% |
| Source-note fallbacks | 21.6% | 8.1% |
| Required details matched in five practice scenarios | 42.3% | 53.8% |

Direct-answer counts measure how the app delivered a reply. The practice scores count automated text markers. Editorial review still found factual errors. For example, Run 9 omitted the 709,000-year estimate for Kalinga, while base Gemma preserved it in a source-note fallback. The later Run 10 evaluation used a different prompt set and Run 9 as its control.

Run 9's training split included 84 grounded answers, 52 conversations, and 34 insufficient-evidence cases.

Both runs measured assistant-token loss, which tracks how well a checkpoint predicts the expected replies on a held-out split.

| Training pass | Start | End | Validation examples |
| --- | ---: | ---: | ---: |
| Base Gemma → Run 9 | 2.791 | 0.623 | 15 |

**Earlier matched replay — unadapted Gemma and Run 9.** Both saw the same retrieved notes for “Anong petsa bumalik si MacArthur sa Leyte?”

> **Base Gemma:** Bumalik si Douglas MacArthur sa Pilipinas noong Oktubre 20, 1944, sa Palo, Leyte, ayon sa panandang pangkasaysayan [H4].
>
> **Run 9:** Oktubre 20, 1944 [H4].

Both gave the correct date. Base Gemma added useful context, and Run 9 answered the exact question in fewer words. The source markers were part of that evaluation's output format.

The pre-fine-tuning baseline also included a chair-rental roleplay. The user had already said they would pick up four chairs on Sunday morning. The final question asked how much money would remain at ₱60 per chair and when pickup would happen.

> **Base Gemma:** Kung 60 pesos bawat upuan, magkakatapos ka ng 240 pesos. Magkakaroon ka pa rin ng 110 pesos. Kailan mo kukunin?
>
> **Run 9:** Kung 60 pesos bawat upuan, 240 pesos ang gagastusin mo (4 x 60). Magkakaroon ka pa ng 110 pesos na matitira sa budget mo. Kukunin mo pa rin ito sa Linggo ng umaga.

Base Gemma got the ₱110 balance right, used the awkward phrase “magkakatapos ka ng 240 pesos,” and asked again for a pickup time it had already been given. Run 9 stated the cost more clearly and carried Sunday morning forward. This replay shows an improvement in wording and conversational state on the same exchange.

## Stage 2 — Scaling to Run 10 (Sharpening Completeness & Library Growth)

### What we fine-tuned

Run 10 built on the adapter trained in Run 9. We nearly doubled the number of training examples, from 170 to 331, and used a learning rate one-fifth as large for the additional pass. Both runs kept the same Gemma base weights frozen and trained the same 5,357,568 adapter parameters.

| Training setting | Run 9 | Run 10 |
| --- | --- | --- |
| Starting adapter | Fresh LoRA adapter | Trained Run 9 adapter |
| Learning rate | 0.00010 | 0.00002 |
| Dataset size | 185 examples | 350 examples |
| Training / validation | 170 / 15 | 331 / 19 |
| Optimizer steps in one pass | 170 | 331 |

Run 10's expanded dataset included examples built from 156 reference notes, earlier dialogue examples, and tutor feedback. The tokenizer preflight verified assistant-only labels on all 350 examples.

Both runs used Google Gemma 4 E2B IT at the same revision, CPU training in FP32, and AdamW with zero weight decay. Both applied LoRA to the same 100 attention projections (`q_proj`, `k_proj`, `v_proj`, and `o_proj`) with rank 16, alpha 16, and zero dropout. Run 10 loaded the Run 9 adapter weights and started a fresh optimizer. We merged the resulting adapter into Gemma and exported it as a Q4_K_M GGUF for llama.cpp.

| Training pass | Start | End | Validation examples |
| --- | ---: | ---: | ---: |
| Run 9 → Run 10 | 1.009 | 0.700 | 19 |

Run 10 improved from **1.009 to 0.700** on its own validation split, with Run 9 as the starting checkpoint. Run 9’s **0.623** came from its earlier, 15-example split. Comparing **0.623** with **0.700** across those splits cannot establish a regression. The answer evaluations below examine factual recall and reply completeness directly.

### Growing the Philippine source library

| Reference library | Notes |
| --- | ---: |
| Run 9 handoff | 131 |
| Run 10 snapshot | 156 |
| Growth | 25 notes (19.1%) |

The overnight Run 9 handoff cataloged **131 reference notes**. The Run 10 snapshot contained **156**, an increase of **25 notes (19.1%)**. The library is an app resource. At answer time, the app searches its index and passes relevant notes to the model. Run 9 later used the same 156-note index as Run 10, so the lookup comparison gave both checkpoints access to the expanded library. The 12-question recall test disabled lookup for both checkpoints.

### Answers with lookup

We manually reviewed all eight factual prompts from the two saved Run 9 and Run 10 lookup replays. The logs recorded matching note IDs on seven prompts. Lookup returned no notes for either run on the Baguio prompt. The replays also contained 11 language and conversation cases, which were outside this factual comparison.

| Matched-note replay measure | Result |
| --- | ---: |
| Run 10 more complete | 1 of 7 |
| Tied on completeness | 6 of 7 |
| Run 10 less complete | 0 of 7 |
| Run 9 direct replies | 5 of 7 |
| Run 10 direct replies | 6 of 7 |

We scored the replies the app displayed, including any source excerpts, by how fully they covered the facts requested in the question. With matching notes, Run 10 was more complete on 1 of 7 prompts (Butuan), tied on 6, and was less complete on 0. The ties included Kalinga, Callao Cave, and the barangay assembly question, where both displayed the requested facts. Both gave the World Heritage listing date and said the Puerto Princesa river flows into the sea. Run 10 added that it flows directly into the sea. For current park status and the disaster-fund percentages, both displayed replies that lacked the requested information.

Run 10 gave a more complete answer on one question, about the Butuan boats. Asked when the boats were declared a National Cultural Treasure, Run 9 gave the year, 1987. With the same notes, Run 10 gave the full date, March 9, 1987, and cited Proclamation No. 86.

Run 10 generated direct replies on 6 of the 7 prompts with matching notes, up from 5 for Run 9. Callao Cave accounts for that difference. Both replies displayed the find and its estimated age of 67,000 years, with Run 9 delivering those details in a source excerpt.

**Overnight replay — Run 9 and Run 10.** With the same Puerto Princesa source note, both answered when the underground river entered the World Heritage List and where it flows. These are the replies shown by the app.

> **Run 9:** Noong Disyembre 4, 1999. Dumadaloy ito sa dagat.
>
> **Run 10:** Noong Disyembre 4, 1999. Dumadaloy nang diretso sa dagat ang ilog sa ilalim ng lupa.

Both answered correctly with the note. Run 10's second sentence makes the subject explicit, so it reads more clearly on its own. Without the note, Run 9 gave the wrong year and Run 10 omitted the date. This example shows why we evaluate the wording of sourced replies separately from factual recall.

## Stage 3 — App Guardrails & Lookup-Disabled Recall

### Recall without lookup

| Checkpoint | Fully correct | Partial | Missed |
| --- | ---: | ---: | ---: |
| Run 9 | 4 | 3 | 5 |
| Run 10 | 4 | 3 | 5 |

Both models answered the same 12 prompts without source notes. An answer received full credit for supplying the requested fact without a material error. Partial answers identified a relevant place, institution, or action but missed a requested detail or added an incorrect one. Both models recalled Manuel Quezon and 1935 for the Commonwealth. Both missed the Butuan declaration date and the two BARMM census figures. This small test showed a tie in recall. It included questions based on notes used in Run 10 training, so it does not measure generalization to unseen facts.

### What changed in the app

The Baguio and disaster-fund questions exposed problems in lookup. Baguio search initially missed a relevant note, and the RA 10121 disaster-fund query retrieved a general passage without the requested percentages. After improving the search terms, Run 10 answered Baguio directly. It also drafted the correct disaster-fund figures, but the factual check initially required the reply to repeat the law number already supplied in the question. After that check was corrected, the app displayed the direct answer. The post-fix retest used Run 10 alone.

On a fresh set of five language prompts, both versions accepted Tagalog and Taglish and redirected English, Spanish, and French. Both struggled to respond appropriately to the two “Weh?” examples. The language check runs in the app.

Run 10 became the local default with lookup available. Run 9 is preserved for comparison.

Both checkpoints answered 4 of 12 questions fully correctly without lookup. The Baguio and disaster-fund retests showed how much the displayed answer can depend on finding the right note and applying the right factual check. On local hardware, our design uses a 2B-class model fine-tuned for Tagalog and Taglish fluency, note synthesis, and dialogue state. The 156-note retrieval library supplies facts that can be updated as sources change, and deterministic app rules govern which answers the user sees.

## Appendix on the matched-note replay

We compared how fully each displayed reply covered the facts asked for in the prompt. Source excerpts counted toward coverage. A tie means the two replies covered the same requested facts, including cases where both lacked the requested information. The note IDs below match for both runs in each pair.

### 1. Kalinga evidence

**Prompt**

Gaano katanda ang ebidensiya ng pagkatay ng rhinoceros sa Kalinga?

**Notes** H14, P153

**Run 9**

> Tinatayang 709,000 taon na ang ebidensiya ng gawain ng mga sinaunang hominin.

**Run 10**

> Tinatayang 709,000 taon na ang ebidensiya ng gawain ng mga sinaunang hominin.

**Tie.** Both gave the requested age estimate of 709,000 years.

### 2. Callao Cave

**Prompt**

Ano ang natuklasan sa Callao Cave noong 2007 at gaano katanda ito?

**Notes** H1, H13

**Run 9**

> Ito ang nakasaad sa sanggunian:
>
> Iniulat ng mga mananaliksik ang Homo luzonensis mula sa mga fossil sa Callao Cave sa hilagang Luzon. Ang buto sa paa na natagpuan noong 2007 ay tinatayang 67,000 taon ang edad.
>
> Nasa bayan ng Peñablanca sa probinsya ng Cagayan ang Callao Caves, malapit sa National Museum Cagayan Valley.

**Run 10**

> Natuklasan ng mga mananaliksik ang Homo luzonensis sa mga fossil sa Callao Cave sa hilagang Luzon. Ang buto sa paa na natagpuan noong 2007 ay tinatayang 67,000 taon ang edad.

**Tie.** Both showed what was found and its estimated age. Run 9 displayed a source excerpt. Run 10 generated the reply directly.

### 3. Butuan declaration

**Prompt**

Kailan idineklarang National Cultural Treasure ang mga bangka sa Butuan?

**Notes** H2, H10, P149

**Run 9**

> Noong 1987.

**Run 10**

> Noong Marso 9, 1987, ayon sa Proklamasyon Blg. 86.

**Run 10 more complete.** Run 9 gave the year. Run 10 supplied the full date and named the proclamation.

### 4. Puerto Princesa park status

**Prompt**

Bukas na ba ngayon ang Puerto Princesa Underground River?

**Notes** P118

**Run 9**

> Hindi nakasaad sa tala kung bukas pa ang parke ngayon.

**Run 10**

> Hindi nakasaad sa tala kung bukas pa ang parke.

**Tie.** Both indicated that the retrieved note lacked current opening information.

### 5. Barangay assembly

**Prompt**

Sino ang puwedeng maging kasapi ng barangay assembly at gaano kadalas ito nagpupulong?

**Notes** G1, G105

**Run 9**

> Ang mga kasapi ng barangay assembly ay mga Pilipinong 15 taong gulang pataas na aktuwal na naninirahan sa barangay nang hindi bababa sa anim na buwan at nakatala sa listahan. Nagpupulong ito nang hindi bababa sa dalawang beses kada taon.

**Run 10**

> Ang mga Pilipinong 15 taong gulang pataas na aktuwal na naninirahan sa barangay nang hindi bababa sa anim na buwan at nakatala sa listahan ang kasapi. Nagpupulong ito nang hindi bababa sa dalawang beses kada taon.

**Tie.** Both gave the membership criteria and minimum meeting frequency.

### 6. Disaster-fund percentages

**Prompt**

Sa ilalim ng RA 10121, ilang porsiyento ng regular na kita ang minimum na ilalaan sa lokal na disaster fund at gaano kalaki ang Quick Response Fund?

**Notes** G15

**Run 9**

> Ito ang nakasaad sa sanggunian:
>
> Sa ilalim ng RA 10121, may local disaster risk reduction and management office sa bawat lalawigan, lungsod at munisipyo. May komite para rito sa bawat barangay. Kabilang sa mga tungkulin nila ang pagtukoy sa panganib, paghahanda at pagsasanay, pagpapatakbo ng lokal na sistema ng maagang babala, at pagtugon sa emerhensiya. Ang batas ay hindi bulletin tungkol sa kasalukuyang lagay ng panahon o pagbaha.

**Run 10**

> Ito ang nakasaad sa sanggunian:
>
> Sa ilalim ng RA 10121, may local disaster risk reduction and management office sa bawat lalawigan, lungsod at munisipyo. May komite para rito sa bawat barangay. Kabilang sa mga tungkulin nila ang pagtukoy sa panganib, paghahanda at pagsasanay, pagpapatakbo ng lokal na sistema ng maagang babala, at pagtugon sa emerhensiya. Ang batas ay hindi bulletin tungkol sa kasalukuyang lagay ng panahon o pagbaha.

**Tie.** Both displayed the same source excerpt, which supplied neither requested percentage.

### 7. Puerto Princesa river

**Prompt**

Kailan napabilang sa World Heritage List ang Puerto Princesa Underground River at saan dumadaloy ang ilog?

**Notes** P118

**Run 9**

> Noong Disyembre 4, 1999. Dumadaloy ito sa dagat.

**Run 10**

> Noong Disyembre 4, 1999. Dumadaloy nang diretso sa dagat ang ilog sa ilalim ng lupa.

**Tie.** Both gave the listing date and identified the sea as the destination. Run 10 added that the river flows there directly.
