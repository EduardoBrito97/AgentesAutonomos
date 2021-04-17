# Agentes Autonomos - II Unidade - StarCraft II
* Oraculo.py = responsável por treinamentos (train()), transdobras (warp_in()) e pesquisas (upgrade)
* Trabalhadores.py = responsável por construções (build()) e captação de recursos (gather()/distribute_workers())
* Soldados.py = responsável por ataque e defesa
* Observadores.py = reponsável por controlar os Observers (scouts)
* ProtossBot.py = script principal para rodar o bot

## Estratégia
* Estruturas
    1. Construir 4 Gateways
    2. Enquanto constrói os Gateways, construir um Cybernetics Core
    3. Usar o Cybernatics Core para fazer a pesquisa para disponibilizar o Warp Gate
    4. Transdobrar os Gateways em Warp Gates
    5. Construir 1 Forge
    6. Realizar as pesquisas de nível 1 da Forge
    7. Enquanto faz as pesquisas, constrói Stargate
    8. Após o Stargate, constrói Fleetbeacon
* Tropas
    1. Produzir Probes até completar o máximo de 16 do Nexus
    2. Usar os Probes para coletar recursos, focando em Minerals no começo e Gas no meio termo
    3. Transdobrar Zealots e Stalkers assim que possível
    4. Assim que possível, transdobrar a Mothership
    5. Atacar se tiver ( (> 5 Zealots e > 5 Stalkers) ou > 10 Zealots) e 1 Mothership e Todas as pesquisas Nv. 1 da Forge
    6. Ao iniciar o ataque, um Probe vai seguir o batalhão de ataque para construir um Pylon de proxy, onde os Warpgates farão as transdobras para perto desse Pylon, pra melhorar o ataque.

## Lista 1 - Início
1. Quais os aspectos mais importantes da mecânica do jogo?
    * Em geral, manejamento de recursos: saber quando parar para pegar minérios, vespeno, gás, etc e o que priorizar para construir.
2. O que é que cada agente percebe e quais são as suas ações?
    * Depende do agente: devemos dividir em, ao menos, dois tipos de agentes:
        * Trabalhadores, que vão ter que saber a quantidade de recurso que temos e se precisamos construir/coletar mais;
        * Soldados, que vão ter que saber se precisamos proteger ou atacar. Dentro desses soldados, teremos diferentes funções para cada um: receber dano, curar, bater... 
3. Que variáveis os agentes vão considerar em sua tomada de decisão?
    * Os trabalhadores devem considerar apenas a prioridade atual para si: construir ou coletar recurso (ou, no caso dos Zergs, se tornar tropas também). 
    * Os soldados devem tomar em consideração se temos quantidade suficiente para realizar um ataque, se estamos sofrendo um ataque, se precisamos ter uma formação ou não.
4. Como é o processo de tomada de decisão?
    * Trabalhadores: Analisar recursos -> Analisar prioridade (construção/coleta/se transformar em tropa) -> Agir (Construir/Coletar recurso).
    * Soldados: Formação -> Analisar se é necessário defender ou atacar -> Agir (Proteger/Atacar/Esperar)
    * Caso algum agente seja atacado em algum momento, transmitir informação de que a base está sob ataque para todos, para que uma defesa seja organizada. Os trabalhadores não precisam necessariamente parar suas atividades, mas os soldados sim.
5. Estas decisões são somente para a próxima ação e/ou são de longo prazo?
    * Os trabalhadores possuem decisões mais relacionadas a próxima ação, enquanto os soldados possuem para ambos: curto e longo prazo.
6. Quão cientes estão os agentes da presença dos outros no ambiente, e que tipo de informações eles trocam?
    * Os trabalhadores estão cientes apenas se estão sob ataque, de quantos recursos temos e qual a prioridade no momento: coletar recurso ou construir. Os soldados trocam informações de quantidade de soldados que possuímos, qual a formação que devem seguir e se estão sob ataque.
7. Como os agentes vão se coordenar? E.g. eles aprendem, planejam juntos, têm protocolo compartilhado, negociam, etc.
    * Planejam juntos para o bem do grupo (cooperativo).
8. Essa coordenação é centralizada, emergente, ou híbrida?
    * Híbrida.
9. Todos os agentes fazem as mesmas coisas? Eles têm os mesmos direitos e deveres?
    * Não.
10. Qual a influência do objetivo do grupo no objetivo individual de cada agente?
    * O objetivo do grupo é o objetivo maior, deve sempre sobressair sobre o desejo individual do agente.