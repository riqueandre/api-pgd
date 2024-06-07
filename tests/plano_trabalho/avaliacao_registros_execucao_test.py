"""Testes para validar a Avaliação de registros de execução do
Plano de Trabalho.
"""

import pytest
from httpx import Client, status

from util import assert_error_message

from .core_test import FIELDS_AVALIACAO_REGISTROS_EXECUCAO

@pytest.mark.parametrize("avaliacao_registros_execucao", [0, 1, 2, 5, 6])
def test_create_pt_invalid_avaliacao_registros_execucao(
    input_pt: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pt,  # pylint: disable=unused-argument
    avaliacao_registros_execucao: int,
    client: Client,
):
    """Testa a criação de um plano de trabalho com um valor inválido para
    o campo avaliacao_registros_execucao.

    O teste envia uma requisição PUT para a rota
    "/organizacao/SIAPE/{cod_unidade_autorizadora}/plano_trabalho/{id_plano_trabalho}"
    com diferentes valores campo avaliacao_registros_execucao.
    Quando o valor for válido (entre 1 e 5), espera-se que a resposta
    tenha o status HTTP 201 Created. Quando o valor for inválido,
    espera-se que a resposta tenha o status HTTP 422 Unprocessable Entity
    e que a mensagem de erro "Avaliação de registros de execução
    inválida; permitido: 1 a 5" esteja presente na resposta.
    """
    input_pt["avaliacao_registros_execucao"][0][
        "avaliacao_registros_execucao"
    ] = avaliacao_registros_execucao

    response = client.put(
        f"/organizacao/SIAPE/{user1_credentials['cod_unidade_autorizadora']}"
        f"/plano_trabalho/{input_pt['id_plano_trabalho']}",
        json=input_pt,
        headers=header_usr_1,
    )

    if avaliacao_registros_execucao in range(1, 6):
        assert response.status_code == status.HTTP_201_CREATED
    else:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "Avaliação de registros de execução inválida; permitido: 1 a 5"
        assert_error_message(response, detail_message)