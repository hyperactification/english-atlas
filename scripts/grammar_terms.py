import re

# The glossary is the only place where Chinese names are intentionally retained.
TERMS = [
('非限制性定语从句','nonrestrictive relative clause'),('限制性定语从句','restrictive relative clause'),
('时间或条件状语从句','adverbial clause of time or condition'),('时间条件状语从句','adverbial clause of time or condition'),
('原因状语从句','adverbial clause of reason'),('条件状语从句','conditional clause'),('时间状语从句','time clause'),('让步状语从句','concessive clause'),
('后置定语从句','relative clause'),('非谓语动词','nonfinite verb'),('过去分词短语','past participle phrase'),('现在分词短语','present participle phrase'),('不定式短语','infinitive phrase'),
('介词宾语','object of a preposition'),('动词宾语','object of a verb'),('宾语补足语','object complement'),('主语补足语','subject complement'),('宾语从句','object clause'),('主语从句','subject clause'),('表语从句','predicative clause'),('同位语从句','appositive clause'),
('真正的主语','real subject'),('真正主语','real subject'),('真实主语','real subject'),('形式主语','formal subject'),('形式宾语','formal object'),
('主谓一致','subject-verb agreement'),('主谓宾结构','SVO structure'),('主系表结构','SVC structure'),('主谓宾','SVO'),('主系表','SVC'),('主谓结构','SV structure'),
('现在完成时','present perfect'),('过去完成时','past perfect'),('一般现在时','simple present'),('一般过去时','simple past'),('一般将来时','simple future'),('将来时','future tense'),
('情态动词','modal verb'),('系动词','linking verb'),('助动词','auxiliary verb'),('实义动词','main verb'),('及物动词','transitive verb'),('不及物动词','intransitive verb'),
('非限制性关系从句','nonrestrictive relative clause'),('定语从句','relative clause'),('关系从句','relative clause'),('关系代词','relative pronoun'),('关系副词','relative adverb'),('连接代词','conjunctive pronoun'),('引导词','clause marker'),('先行词','antecedent'),
('后置形容词短语','postmodifying adjective phrase'),('形容词短语','adjective phrase'),('介词短语','prepositional phrase'),('动名词短语','gerund phrase'),('名词短语','noun phrase'),('分词短语','participle phrase'),
('不可数名词','uncountable noun'),('单数可数名词','singular countable noun'),('可数名词','countable noun'),('可数复数','plural countable form'),('集合名词','collective noun'),('抽象名词','abstract noun'),
('完全倒装','full inversion'),('部分倒装','partial inversion'),('双重否定','double negation'),('部分否定','partial negation'),('全部否定','total negation'),
('被动语态','passive voice'),('主动语态','active voice'),('并列谓语','coordinated predicates'),('并列宾语','coordinated objects'),('并列结构','coordination'),
('前置定语','premodifier'),('后置定语','postmodifier'),('目的状语','purpose adverbial'),('方式状语','manner adverbial'),('原因状语','reason adverbial'),('时间状语','time adverbial'),('条件状语','condition adverbial'),('让步状语','concession adverbial'),('伴随状语','accompanying adverbial'),('程度状语','degree adverbial'),('范围状语','scope adverbial'),('状语从句','adverbial clause'),
('现在分词','present participle'),('过去分词','past participle'),('动名词','gerund'),('不定式','infinitive'),('非谓语','nonfinite structure'),
('限定词','determiner'),('冠词','article'),('定冠词','definite article'),('不定冠词','indefinite article'),('所有格','possessive'),('人称代词','personal pronoun'),('代词','pronoun'),('指示代词','demonstrative pronoun'),
('并列连词','coordinating conjunction'),('连词','conjunction'),('动词','verb'),('形容词','adjective'),('副词','adverb'),('名词','noun'),('介词','preposition'),('分词','participle'),
('从句','clause'),('主句','main clause'),('主干','sentence core'),('主语','subject'),('谓语','predicate'),('宾语','object'),('表语','subject complement'),('补足语','complement'),('定语','modifier'),('状语','adverbial'),
('单复数同形','same singular and plural forms'),('第三人称单数','third-person singular'),('单数','singular'),('复数','plural'),('不可数','uncountable'),('可数','countable'),
('词性','part of speech'),('否定句','negative sentence'),('疑问句','interrogative sentence'),('陈述句','declarative sentence'),('祈使句','imperative sentence'),('时态','tense'),('语态','voice'),('倒装','inversion'),('省略句','elliptical clause'),('句型','sentence pattern'),('语法','grammar')]
TERMS += [('前置修饰语','premodifier'),('后置修饰语','postmodifier'),('逻辑主语','logical subject'),('直接宾语','direct object'),('间接宾语','indirect object'),('动词原形','base form'),('被动句','passive sentence'),('主动句','active sentence'),('被动谓语','passive predicate'),('被动结构','passive structure'),('被动关系','passive relationship'),('被动形式','passive form'),('主动形式','active form'),('主动关系','active relationship'),('主动式','active form'),('被动式','passive form'),('被动标记','passive marker'),('被动修饰','passive modification'),('否定祈使','negative imperative'),('否定前缀','negative prefix'),('前缀','prefix'),('后缀','suffix'),('中心词','head word'),('主谓关系','subject-predicate relationship'),('过去式','past tense form'),('并列主语','coordinated subjects'),('否定词','negative word'),('存在句','existential construction'),('补足成分','complement')]
TERMS.append(('单复数','singular and plural forms'))
TERMS.sort(key=lambda x:len(x[0]),reverse=True)
RX=re.compile('|'.join(re.escape(x[0]) for x in TERMS))
T=dict(TERMS)
def english_terms(text):
    return RX.sub(lambda m:' '+T[m[0]]+' ',text).strip()

