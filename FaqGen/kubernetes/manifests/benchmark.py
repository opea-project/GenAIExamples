import argparse
import concurrent.futures
import json
import random
import time

import numpy
import requests
#from transformers import AutoModelForCausalLM, AutoTokenizer

# tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2-7B-Instruct")

query_128 = "In a world where technology has advanced beyond our wildest dreams, humanity stands on the brink of a new era. The year is 2050, and artificial intelligence has become an integral part of everyday life. Autonomous vehicles zip through the streets, drones deliver packages with pinpoint accuracy, and smart homes anticipate every need of their inhabitants. But with these advancements come new challenges and ethical dilemmas. As society grapples with the implications of AI, questions about privacy, security, and the nature of consciousness itself come to the forefront. Amidst this backdrop, a new breakthrough in quantum computing promises to revolutionize the field even further."

# tokens = tokenizer.encode(query_128)
# num_tokens = len(tokens)
# #print(num_tokens)


# tokens of query is 512
query = "In a world where technology has advanced beyond our wildest dreams, humanity stands on the brink of a new era. The year is 2050, and artificial intelligence has become an integral part of everyday life. Autonomous vehicles zip through the streets, drones deliver packages with pinpoint accuracy, and smart homes anticipate every need of their inhabitants. But with these advancements come new challenges and ethical dilemmas. As society grapples with the implications of AI, questions about privacy, security, and the nature of consciousness itself come to the forefront. Amidst this backdrop, a new breakthrough in quantum computing promises to revolutionize the field even further. Scientists have developed a quantum processor capable of performing calculations at speeds previously thought impossible. This leap in technology opens the door to solving problems that have long stumped researchers, from predicting climate change patterns with unprecedented accuracy to unraveling the mysteries of the human genome. However, the power of this new technology also raises concerns about its potential misuse. Governments and corporations race to secure their own quantum capabilities, sparking a new kind of arms race. Meanwhile, a group of rogue programmers, known as the Shadow Collective, seeks to exploit the technology for their own ends. As tensions rise, a young scientist named Dr. Evelyn Zhang finds herself at the center of this unfolding drama. She has discovered a way to harness quantum computing to create a true artificial general intelligence (AGI), a machine capable of independent thought and reasoning. Dr. Zhang's creation, named Athena, possesses the potential to either save humanity from its own worst impulses or to become the ultimate instrument of control. As she navigates the treacherous waters of corporate espionage, government intrigue, and ethical quandaries, Dr. Zhang must decide the fate of her creation and, with it, the future of humanity. Will Athena be a benevolent guardian or a malevolent dictator? The answer lies in the choices made by those who wield its power. The world watches with bated breath as the next chapter in the saga of human and machine unfolds. In the midst of these global tensions, everyday life continues. Children attend schools where AI tutors provide personalized learning experiences. Hospitals use advanced algorithms to diagnose and treat patients with greater accuracy than ever before. The entertainment industry is transformed by virtual reality experiences that are indistinguishable from real life."
my_query = "What is Deep Learning?"
query_rerank_1 = """Deep learning is a subset of machine learning, which itself is a branch of artificial intelligence (AI). It involves the use of neural networks with many layers—hence "deep." These networks are capable of learning from data in a way that mimics human cognition to some extent. The key idea is to create a system that can process inputs through multiple layers where each layer learns to transform its input data into a slightly more abstract and composite representation. In a typical deep learning model, the input layer receives the raw data, similar to the way our senses work. This data is then passed through multiple hidden layers, each of which transforms the incoming data using weights that are adjusted during training. These layers might be specialized to recognize certain types of features in the data, like edges or textures in an image, specific words or phrases in a text, or particular frequency patterns in audio. The final layer produces the output of the model, which could be a class label in classification tasks, a continuous value in regression, or a complex pattern in generative models. Deep learning has been behind many of the recent advancements in AI, including speech recognition, image recognition, natural language processing, and autonomous driving."""
query_rerank_2 = """Deep learning is a powerful tool in the field of artificial intelligence, but it's important to recognize what it is not. Deep learning is not a solution to all types of data processing or decision-making problems. While deep learning models excel at tasks involving large amounts of data and complex patterns, they are not as effective for tasks that require reasoning, logic, or understanding of abstract concepts, which are better handled by other types of AI algorithms. Deep learning is also not a synonym for all of machine learning. Traditional machine learning encompasses a broader range of techniques that include not only neural networks but also methods like decision trees, support vector machines, and linear regression. These traditional models often require less data and computational power and can be more interpretable than deep learning models. They are particularly useful in scenarios where the underlying relationships in the data are more straightforward or where transparency in decision-making is critical. Additionally, deep learning is not inherently unbiased or fair. The models can perpetuate or even amplify biases present in the training data, leading to unfair outcomes in applications like hiring, lending, and law enforcement."""
# tokens of query is 1k
query_llm = "In a world where technology has advanced beyond our wildest dreams, humanity stands on the brink of a new era. The year is 2050, and artificial intelligence has become an integral part of everyday life. Autonomous vehicles zip through the streets, drones deliver packages with pinpoint accuracy, and smart homes anticipate every need of their inhabitants. But with these advancements come new challenges and ethical dilemmas. As society grapples with the implications of AI, questions about privacy, security, and the nature of consciousness itself come to the forefront. Amidst this backdrop, a new breakthrough in quantum computing promises to revolutionize the field even further. Scientists have developed a quantum processor capable of performing calculations at speeds previously thought impossible. This leap in technology opens the door to solving problems that have long stumped researchers, from predicting climate change patterns with unprecedented accuracy to unraveling the mysteries of the human genome. However, the power of this new technology also raises concerns about its potential misuse. Governments and corporations race to secure their own quantum capabilities, sparking a new kind of arms race. Meanwhile, a group of rogue programmers, known as the Shadow Collective, seeks to exploit the technology for their own ends. As tensions rise, a young scientist named Dr. Evelyn Zhang finds herself at the center of this unfolding drama. She has discovered a way to harness quantum computing to create a true artificial general intelligence (AGI), a machine capable of independent thought and reasoning. Dr. Zhang's creation, named Athena, possesses the potential to either save humanity from its own worst impulses or to become the ultimate instrument of control. As she navigates the treacherous waters of corporate espionage, government intrigue, and ethical quandaries, Dr. Zhang must decide the fate of her creation and, with it, the future of humanity. Will Athena be a benevolent guardian or a malevolent dictator? The answer lies in the choices made by those who wield its power. The world watches with bated breath as the next chapter in the saga of human and machine unfolds. In the midst of these global tensions, everyday life continues. Children attend schools where AI tutors provide personalized learning experiences. Hospitals use advanced algorithms to diagnose and treat patients with greater accuracy than ever before. The entertainment industry is transformed by virtual reality experiences that are indistinguishable from real life. Yet, for all the benefits, there are those who feel left behind by this technological revolution. Communities that once thrived on traditional industries find themselves struggling to adapt. The digital divide grows wider, creating new forms of inequality. Dr. Zhang's journey is not just a scientific quest but a deeply personal one. Her motivations are shaped by a desire to honor her late father's legacy, a pioneer in the field of AI who envisioned a future where technology would serve humanity's highest ideals. As she delves deeper into her research, she encounters allies and adversaries from unexpected quarters. A former colleague, Dr. Marcus Holt, now working for a rival tech giant, becomes both a rival and a potential ally as they navigate their complex relationship. In a hidden lab, far from prying eyes, Dr. Zhang and her team work tirelessly to refine Athena. They face numerous setbacks and breakthroughs, each step bringing them closer to their goal. The ethical implications of their work weigh heavily on them. Can a machine truly understand human emotions? Is it possible to program empathy and compassion? These questions haunt Dr. Zhang as she watches Athena's capabilities grow. As word of Athena's development leaks, the world reacts with a mixture of hope and fear. Protests erupt in major cities, with demonstrators demanding transparency and ethical oversight. Governments convene emergency sessions to discuss the potential impact of AGI on national security and global stability. Amid the chaos, the Shadow Collective launches a cyber-attack on Dr. Zhang's lab, attempting to steal her research. The attack is thwarted, but it serves as a stark reminder of the dangers they face. The final phase of Athena's development involves a series of tests to evaluate her decision-making abilities. Dr. Zhang designs scenarios that challenge Athena to balance competing interests and make ethical choices. In one test, Athena must decide whether to divert a runaway trolley to save a group of people at the expense of one individual. In another, she is tasked with allocating limited medical resources during a pandemic. Each test pushes the boundaries of machine ethics and highlights the complexities of programming morality. Summarize the story above."
# length of my_embedding is 768
my_embedding = [0.00030903306,-0.06356524,0.0025720573,-0.012404448,0.050649878,0.023426073,0.022131812,0.000759529,-0.00021144224,-0.03351229,-0.024963351,0.0064628883,-0.007054883,0.066674456,0.0013026494,0.046839874,0.06272031,-0.021033816,0.011214508,0.043999936,-0.050784662,-0.06221004,-0.04018244,0.017779319,-0.0013301502,0.0022156204,-0.043744676,0.012752031,-0.023972677,0.011199989,0.028703978,-0.0089899,0.03712499,-0.027488017,0.016138831,0.041751742,-0.03958115,-0.03528769,-0.022453403,-0.019844962,-0.018594252,-0.042406067,-0.0120475935,0.049004447,-0.08094748,0.017947419,-0.12090019,0.0023762283,-0.022721844,-0.0122670885,-0.07537693,0.051195897,0.032084838,-0.0191422,0.042885557,0.0152152525,0.0042946604,-0.08067345,0.010296512,-0.05629215,0.051881734,0.037080515,-0.018511552,-0.027629064,-0.0010543121,-0.02618493,0.024228664,0.042858265,-0.02330382,-0.0034123377,-0.028686361,0.029237133,-0.020652898,-0.005005634,-0.052511718,-0.011031183,0.012807135,0.0143450685,0.08218706,-0.008386834,0.0036734014,0.06236072,0.04255367,0.03158083,0.004631116,0.0007993413,-0.019410692,-0.004640353,-0.044894144,0.022581149,0.010380893,-0.053084206,0.060135297,0.051447738,0.014172936,0.0076013976,0.01375325,-0.035371594,-0.011681993,-0.014776056,-0.023268431,-0.0590664,-0.016947128,-0.0146322865,-0.048343826,0.026675656,0.052418776,-0.013986488,0.014608619,-0.019658033,-0.0014043319,-0.008499042,-0.0025460746,-0.04858996,-0.04293979,-0.00791175,-0.01644228,0.0038053868,-0.025010196,-0.04599194,0.03430527,0.0382939,0.0019500003,0.021234535,-0.03411336,0.015422987,0.0040041124,0.018236278,0.004566607,-0.02694257,0.020603696,0.0168677,-0.007864176,0.02186715,-0.014774427,0.00078197615,-0.020355146,0.006654448,0.025772778,0.009957317,-0.0025282202,-0.0579994,0.030099394,-0.03549671,0.05439607,-0.015254235,-0.007988717,-0.004305188,-0.018912116,0.0027841094,-0.044504374,0.05556499,-0.018894102,-0.049442377,0.008305442,0.039805025,-0.00042916916,0.0059957127,0.034555893,0.02306613,0.05890197,-0.019604865,-0.05472663,-0.009928875,-0.02455136,-0.054289207,0.055403363,0.024503028,-0.019979116,0.025056925,-0.0020133695,-0.011331945,0.020181546,-0.012020893,0.011718686,0.047295712,0.028600235,0.034037635,0.043115,0.051445063,-0.065478735,0.046462707,-0.00893844,-0.0063705654,-0.044797033,-0.03157799,0.04950285,-0.010792562,0.03688506,0.014347515,-0.063743494,-0.036214367,-0.03380074,-0.03769261,0.033050846,-0.016999796,-0.015086913,0.082186624,-0.011051229,0.04645044,0.054343436,-0.05152064,0.015258479,-0.016340451,-0.027205588,0.029828794,0.01575663,-0.04375617,-0.003217223,0.0033928305,0.0076283724,-0.049442016,-0.0053870296,0.001464261,0.043246116,0.030448606,-0.007991404,-0.00472732,0.0065691406,-0.018045014,0.0050486918,-0.042211313,0.024785575,0.002973673,0.008309046,0.08794761,0.041150656,-0.051644977,0.03518446,-0.037274398,0.003677234,0.02468397,-0.012616027,0.019353414,0.013835055,-0.027715908,0.014544011,0.0104869455,0.04520827,-0.03349062,-0.070577316,0.006990252,-0.047459435,0.05270745,0.011758987,0.009585331,0.033369783,-0.014058916,-0.01459581,-0.016755696,-0.004542376,0.00010269242,0.016674489,0.029076884,-0.02398147,-0.059065636,0.0021090624,-0.009751267,0.10289938,0.027459696,-0.050843943,0.051473383,-0.027577678,0.022293199,-0.02546725,-0.095162235,-0.02834687,-0.020029712,0.08765645,-0.014138398,0.048151582,0.0074673486,0.03930912,8.716728e-05,-0.026958048,0.0055812267,0.054877758,0.055222698,-0.012584492,-0.04345845,-0.02426138,0.066533394,0.0056506116,-0.015095139,0.027254738,-0.025936818,-0.0030386604,-0.008605405,-0.00891901,0.0043280497,0.03594552,0.061649352,-0.042369556,0.048818704,0.021097481,0.053623416,0.045890126,-0.02760507,-0.01573271,8.311729e-05,-0.007044427,0.039558847,-0.021737648,0.03881644,0.020095227,-0.0130994925,0.07956597,-0.014619613,-0.196594,-0.012995427,0.017993039,-0.0073582316,0.03813464,-0.05930209,-0.005811095,-0.009954021,0.0018040026,-0.02305836,-0.027102914,-0.006594491,0.03801163,0.025225805,0.019853814,-0.01661875,0.00875584,-0.016539048,-0.036775734,0.045325384,-0.031573802,-0.029247303,-0.01253526,0.07143945,-0.029145112,0.027142324,-0.084799446,-0.05071047,-0.0028705404,-0.0021605634,-0.023848932,-0.028478833,-0.0324437,0.04862323,0.023280755,0.016372373,0.027676713,-0.03990074,-0.002498963,0.017739112,-0.03355715,-0.048603803,0.003019928,-0.040887985,0.044802677,0.015728928,-0.09309996,-0.04836613,-0.014831327,0.0010454153,-0.010638626,-0.024611702,-0.06786172,-0.0013613648,0.015592544,-0.004870558,0.0025347366,-0.012121049,-0.024824884,0.036656864,-0.0031881756,-0.020234713,-0.02279762,-0.05922489,-0.020922685,-0.02317517,-0.0610787,-0.062339265,0.017110312,0.03338325,-0.010112536,0.048114073,-0.06444785,-0.04852081,0.006865087,-0.025729232,-0.029516479,-0.00941828,0.05484419,0.027107889,0.008253239,-0.06284466,0.035466067,0.012162117,-0.009598869,-0.048561577,0.046412956,-0.03714821,-0.020295296,-0.028690876,0.06459795,-0.006428147,-0.026629865,-0.026355268,0.03504117,0.019873064,0.0032821875,0.028802538,-0.013105742,0.019568242,-0.021279998,-0.024270158,-0.04382199,-0.016565602,-0.040926415,-0.022030178,-0.009905917,0.030040652,0.10125908,-0.00263213,-0.037816163,0.014336923,0.025456406,0.00100471,0.00032630135,-0.030703938,0.016242733,0.0013898151,0.018662402,-0.038746417,-0.03208466,0.05599271,0.0056110374,0.04541296,0.015634691,-0.0295602,0.0008552127,0.0152370455,0.01917365,-0.025870943,0.020953277,-0.0003668304,0.012462414,0.008920647,-0.0016022202,-0.012868524,-0.010962337,-0.0068797423,-0.009876324,0.009545094,-0.0076226145,0.0016608062,0.01671912,-0.015954005,-0.020932103,0.049466487,-0.073524654,0.060834516,-0.0069076903,-0.014720568,0.014687667,-0.028758403,0.025296489,-0.058295064,0.0300228,-0.0070548407,0.010030844,-0.0065278015,-0.028693652,-0.04413148,0.010020056,0.03030962,-0.009985439,0.0104528945,0.055963244,0.054369748,-0.026280807,-0.061695196,0.03131826,0.012127447,0.034067005,-0.029661555,-0.008471412,-0.031715434,-0.014869134,0.036652327,0.026443308,-0.005586143,0.02489041,0.058810584,0.017560603,0.039287437,-0.0034399417,0.033162847,0.050130997,0.032992795,-0.029766096,0.0061241565,-0.055100117,0.028030321,-0.038325004,0.024334624,-0.017313298,-0.019499615,-0.01981792,-0.027658446,-0.018781614,0.047175173,-0.0034721645,-0.020667735,-0.039781824,-0.019210767,-0.026337992,-0.023234084,0.04964025,-0.07777429,0.030660955,0.048808888,0.044913623,0.03674177,-0.011647912,-0.02756851,-0.07255596,-0.087645784,-0.039343175,-0.04203861,-0.0039666323,0.01671798,0.026770905,-0.03026136,0.029986707,0.024289394,0.0117887445,-0.012229226,-0.047474023,-0.03667933,0.026632814,0.03635988,0.0005169153,0.017991144,0.009195582,-0.0069137816,0.011830262,-0.005349248,-0.034725383,0.031615537,-0.05287625,0.014696611,-0.014054976,-0.016312832,0.0019933872,0.02526325,-0.07060638,0.010108201,-0.014116627,-0.0059261527,-0.008993763,0.021177163,-0.04376879,-0.028056782,0.06090816,0.0039020707,-0.038584042,-0.048930347,0.023969071,-0.059767634,-0.029087082,-0.055471163,-0.0693663,-0.005782939,-0.02213406,-0.008931021,-0.0056467317,0.029872,0.022359788,0.008790491,-0.03974519,-0.0064023994,0.065675184,-0.01572894,-0.03746496,-0.061758112,-0.028639734,0.08637485,0.031286176,-0.0007831992,0.0030584438,0.012293266,0.020008529,-0.028351337,0.0020157974,0.027084284,0.0027892909,-0.03614263,0.006040403,-0.0475395,-0.004725341,-0.021484248,-0.022895435,-0.015276968,-0.04321307,-0.04412736,-0.005665974,-0.009453732,-0.028690176,0.010030023,0.027899086,0.060336158,0.06936418,0.006905735,-0.024200331,0.04907079,0.0031401473,0.00441764,-0.029459601,0.03803177,-0.0353827,-0.04895069,0.04761868,0.007312183,-0.008343287,-0.035251893,0.036832787,0.0246635,-0.03892744,0.018956844,0.013805393,-0.048437007,-0.04829463,0.022492649,-0.029296776,0.041375805,0.046585515,0.020296978,0.03789685,0.059837162,0.011104047,-0.032134652,0.07064702,0.04802412,0.01730015,0.07398111,-0.049616653,0.073309965,-0.009425022,-0.06281925,0.024277369,0.021769999,0.018801004,0.020460334,-0.017282128,0.02107381,0.050663974,0.05384202,-0.015786275,0.054115638,0.051110543,0.07228662,-0.0297164,0.048188735,0.0064821052,-0.025109168,0.013359567,-0.021189261,0.025518114,-0.048609257,0.035189547,0.08076792,0.0037926896,-0.015581124,0.0021879557,0.03258444,0.1159761,-0.021879155,-0.029991308,0.016155615,-0.0064807986,-0.06050641,-0.0056326366,0.028292047,-0.02181108,0.032760337,-0.02199964,-0.034708463,0.011786828,-0.035356887,-0.014913256,-0.039785992,-0.021320345,0.026806,-0.002236271,0.044643793,-0.015494709,-0.0065790443,0.0066197272,-0.0050217584,-0.077643394,0.054302536,0.02795664,-0.03983502,-0.027030395,-0.024944995,-0.0022802327,0.07870793,-0.034157082,0.037108578,0.044204045,0.012753803,0.0037155224,0.008254912,0.013719737,-0.010619027,-0.021691227,0.05794269,-0.075987175,-0.054171626,0.0038932571,0.0039806664,-0.037909392,-0.030339854,0.063346766,-0.088324875,-0.06095589,0.08515697,0.020457987,0.080888115,0.032549396,0.003924944,0.029362155,0.012281526,-0.06369542,0.023577815,-0.017478395,-0.0016188929,0.01734596,0.043068424,0.049590185,0.028447397,0.021328118,-0.0025053236,-0.030895222,-0.055287424,-0.045610603,0.04216762,-0.027732681,-0.036629654,0.028555475,0.066825,-0.061748896,-0.08889239,0.045914087,-0.004745301,0.034891862,-0.0065364013,-0.0069724764,-0.061335582,0.02129905,-0.02776986,-0.0246678,0.03999176,0.037477136,-0.006806653,0.02261455,-0.04570737,-0.033122733,0.022785513,0.0160026,-0.021343587,-0.029969815,-0.0049176104]

faq_demo = "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."

DATAS = {
    "tei_embedding": {"inputs": query_128},
    "mosec_embedding": {"input": query_128, "model": "bce"},
    "embedding": {"text": query},
    "guardrail": {"text": "How do you buy a tiger in the US?"},
    "retrieval": {"text": my_query, "embedding": my_embedding},
    "tei_rerank": {"query": my_query, "texts": [query_rerank_1, query_rerank_2]},
    "mosec_rerank": {"query": my_query, "texts": [query_rerank_1, query_rerank_2]},
    "reranking": {"initial_query": my_query, "retrieved_docs": [{"text": query_rerank_1},{"text": query_rerank_2}]},
    "tgi": {"inputs": query_llm, "parameters":{"max_new_tokens":128}},
    "llm": {"query": query_llm, "max_new_tokens": 128},
    "rag": {"messages": query_llm, "max_tokens": 1024},
    "codetrans": {"language_from": "Java","language_to": "Python","source_code": "'''public class StringReverseExample{\npublic static void main(String[] args){\n  String string=\"runoob\";\n  String reverse = new StringBuffer(string).reverse().toString();\n  System.out.println(\"before reverse:\"+string);\n  System.out.println(\"after reverse:\"+reverse);\n  }\n}'''"},
    "faq": {"messages": faq_demo, "max_tokens": 1024}
}

def send_single_request(task, idx, queries, concurrency, url):
    res = []
    headers = {"Content-Type": "application/json"}
    data = DATAS[task]
    while idx < len(queries):
        start_time = time.time()
        response = requests.post(url, json=data, headers=headers)
        end_time = time.time()
        res.append({"idx": idx, "start": start_time, "end": end_time})
        idx += concurrency
        print(response.content)
    return res


def send_concurrency_requests(task, request_url, num_queries):
    if num_queries <= 4:
        concurrency = 1
    else:
        concurrency = num_queries // 4
    responses = []
    stock_queries = [query for _ in range(num_queries)]
    test_start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        for i in range(concurrency):
            futures.append(executor.submit(
                send_single_request,
                task=task,
                idx=i,
                queries=stock_queries,
                concurrency=concurrency,
                url=request_url
            ))
        for future in concurrent.futures.as_completed(futures):
            responses = responses + future.result()
    test_end_time = time.time()

    print("=======================")
    for r in responses:
        r["total_time"] = r["end"] - r["start"]
        print("query:", r["idx"], "    time taken:", r["total_time"])

    print("=======================")
    print(f"Total Concurrency: {concurrency}")
    print(f"Total Requests: {len(stock_queries)}")
    print(f"Total Test time: {test_end_time - test_start_time}")

    response_times = [r["total_time"] for r in responses]

    # Calculate the P50 (median)
    p50 = numpy.percentile(response_times, 50)
    print("P50 total latency is ", p50, "s")

    # Calculate the P99
    p99 = numpy.percentile(response_times, 99)
    print("P99 total latency is ", p99, "s")

    return p50, p99

def send_single_request_zh(task, idx, queries, concurrency, url, data_zh=None):
    res = []
    headers = {"Content-Type": "application/json"}
    query = random.choice(data_zh)
    data ={"messages": query, "max_tokens": 128} 
    if task == "rag":
        data = {"messages": query, "max_tokens": 128}
    elif task == "embedding":
        data = {"text": query}
    elif task == "llm":
        data = {"query": query, "max_new_tokens": 128}
    print(data)
    while idx < len(queries):
        start_time = time.time()
        response = requests.post(url, json=data, headers=headers)
        end_time = time.time()
        res.append({"idx": idx, "start": start_time, "end": end_time})
        idx += concurrency
        print(response.content)
    return res


def send_concurrency_requests_zh(task, request_url, num_queries):
    if num_queries <= 4:
        concurrency = 1
    else:
        concurrency = num_queries // 4
        
    data_zh = []
    file_path = './stress_benchmark/data_zh.txt'
    with open(file_path, 'r') as file:
        for line in file:
            data_zh.append(line.strip())

    responses = []
    stock_queries = [query for _ in range(num_queries)]
    test_start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        for i in range(concurrency):
            futures.append(executor.submit(
                send_single_request_zh,
                task=task,
                idx=i,
                queries=stock_queries,
                concurrency=concurrency,
                url=request_url,
                data_zh=data_zh
            ))
        for future in concurrent.futures.as_completed(futures):
            responses = responses + future.result()
    test_end_time = time.time()

    print("=======================")
    for r in responses:
        r["total_time"] = r["end"] - r["start"]
        print("query:", r["idx"], "    time taken:", r["total_time"])

    print("=======================")
    print(f"Total Concurrency: {concurrency}")
    print(f"Total Requests: {len(stock_queries)}")
    print(f"Total Test time: {test_end_time - test_start_time}")

    response_times = [r["total_time"] for r in responses]

    # Calculate the P50 (median)
    p50 = numpy.percentile(response_times, 50)
    print("P50 total latency is ", p50, "s")

    # Calculate the P99
    p99 = numpy.percentile(response_times, 99)
    print("P99 total latency is ", p99, "s")

    return p50, p99


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Concurrent client to send POST requests")
    parser.add_argument("--task", type=str, default="faq", help="Task to perform")
    parser.add_argument("--url", type=str, default="http://localhost:8080", help="Service URL")
    parser.add_argument("--num-queries", type=int, default=128, help="Number of queries to be sent")
    parser.add_argument("--zh", help="data_zh", action="store_true")
    args = parser.parse_args()

    if args.zh:
        send_concurrency_requests_zh(args.task, args.url, args.num_queries)
    else:        
        send_concurrency_requests(args.task, args.url, args.num_queries)
    

