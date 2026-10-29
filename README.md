# KAY-Test-Runner

Infraestrutura exclusiva para testes remotos de c?digo sint?tico, sem segredos.

## Estado inicial

Somente infraestrutura. Nenhum pacote de programa??o est? publicado.
A presen?a deste workflow n?o autoriza dispar?-lo. N?o executar workflows nesta etapa.

## Execu??o futura autorizada

Somente workflow_dispatch; n?o h? gatilhos push, pull_request ou schedule.
Python 3.12, depend?ncias predefinidas, comando fixo python -m pytest -q.
Runner padr?o ubuntu-24.04; timeout do job de tr?s minutos; uma execu??o por grupo.
GITHUB_TOKEN somente contents: read, sem credenciais persistidas no checkout.
Artefatos com reten??o de um dia e logs de teste limitados.

A rede do runner N?O est? bloqueada. O controlador n?o ? sandbox para c?digo hostil.
Aceitar somente arquivos sint?ticos revisados e sem credenciais ou dados de produ??o.
A App de automa??o deve ser separada, instalada somente neste reposit?rio.
N?o cadastrar secrets personalizados, ambientes de produ??o, deploy ou runners pagos.

## Limites

Nenhum push, merge ou deploy de projeto operacional ? feito pelo controlador.
Cada pacote futuro ter? commit e refer?ncia exclusivos, dois arquivos permitidos e manifesto.
O KAY exige autoriza??o espec?fica antes da publica??o e do disparo; n?o repete dispatch incerto.
Resultados devem ser revisados pelo operador. N?o h? execu??o recorrente ou rerun autom?tico.

Custos e armazenamento devem ser conferidos pelo propriet?rio antes de qualquer teste.
N?o habilitar recursos pagos. Configurar reten??o de logs do reposit?rio em um dia.
