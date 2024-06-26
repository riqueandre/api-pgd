"""Módulo que define os esquemas de validação dos dados recebidos pela
API.

A principal ferramenta de validação de dados usada no FastAPI é o
Pydantic: https://docs.pydantic.dev/2.0/
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, EmailStr
from pydantic import model_validator, field_validator

from models import (
    PlanoEntregas,
    Entrega,
    TipoMeta,
    PlanoTrabalho,
    Contribuicao,
    TipoContribuicao,
    AvaliacaoRegistrosExecucao,
    Participante,
    ModalidadesExecucao,
    Users,
)
from util import over_a_year

STR_FIELD_MAX_SIZE = 300


# Função para validar CPF
def cpf_validate(input_cpf: str) -> str:
    """Verifica se um número de CPF em forma de string tem o formato
    esperado e também os dígitos verificadores.

    Args:
        input_cpf (str): O número CPF a ser verificado.

    Raises:
        ValueError: CPF deve conter apenas dígitos.
        ValueError: CPF precisa ter 11 dígitos.
        ValueError: CPF com o mesmo número repetido.
        ValueError: CPF com dígitos verificadores inválidos.

    Returns:
        str: O mesmo que a entrada, se for validado.
    """
    if not input_cpf.isdigit():
        raise ValueError("CPF deve conter apenas dígitos.")

    cpf = [int(char) for char in input_cpf if char.isdigit()]
    #  Verifica se o CPF tem 11 dígitos
    if len(cpf) != 11:
        raise ValueError("CPF precisa ter 11 dígitos.")

    #  Verifica se o CPF tem todos os números iguais, ex: 111.111.111-11
    #  Esses CPFs são considerados inválidos mas passam na validação dos dígitos
    if len(set(cpf)) == 1:
        raise ValueError("CPF inválido.")

    #  Valida os dois dígitos verificadores
    for i in range(9, 11):
        value = sum((cpf[num] * ((i + 1) - num) for num in range(0, i)))
        digit = ((value * 10) % 11) % 10
        if digit != cpf[i]:
            raise ValueError("Dígitos verificadores do CPF inválidos.")

    return input_cpf


class ContribuicaoSchema(BaseModel):
    __doc__ = Contribuicao.__doc__
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = Field(
        default=None,
        title="ID da Contribuição",
        description=Contribuicao.id.comment,
    )
    id_contribuicao: str = Field(
        title="Identificador único da contribuição",
        description=Contribuicao.id_contribuicao.comment,
    )
    cod_unidade_instituidora: int = Field(
        title="Código da unidade organizacional (UORG)",
        description=Contribuicao.cod_unidade_instituidora.comment,
    )
    tipo_contribuicao: TipoContribuicao = Field(
        title="Tipo de contribuição",
        description=Contribuicao.tipo_contribuicao.comment,
    )
    percentual_contribuicao: int = Field(
        title="Percentual de contribuição",
        description=Contribuicao.percentual_contribuicao.comment,
    )
    origem_unidade_entrega: Optional[str] = Field(
        title="Código do sistema da unidade do Plano de Entregas da "
        "Entrega, quando a Contribuição for para uma Entrega externa.",
        description=Contribuicao.origem_unidade_entrega.comment,
    )
    cod_unidade_autorizadora_entrega: Optional[int] = Field(
        default=None,
        title="Código da unidade organizacional (UORG) da unidade "
        "autorizadora do Plano de Entregas da Entrega, quando a Contribuição "
        "for para uma Entrega externa.",
        description=Contribuicao.cod_unidade_autorizadora_entrega.comment,
    )
    id_plano_entregas: Optional[str] = Field(
        default=None,
        title="Identificador único do plano de entrega",
        description=Contribuicao.id_plano_entregas.comment,
    )
    id_entrega: Optional[str] = Field(
        default=None,
        title="Identificador único da entrega",
        description=Contribuicao.id_entrega.comment,
    )

    @field_validator("tipo_contribuicao")
    @staticmethod
    def validate_tipo_contribuicao(tipo_contribuicao: TipoContribuicao):
        "Valida se o tipo de contribuição é válido (entre 1 e 3)."
        if tipo_contribuicao not in set(TipoContribuicao):
            raise ValueError("Tipo de contribuição inválido; permitido: 1 a 3")
        return tipo_contribuicao

    @model_validator(mode="after")
    def validate_cod_unidade_autorizadora_entrega(self) -> "ContribuicaoSchema":
        if (
            self.tipo_contribuicao
            not in (
                TipoContribuicao.entrega_propria_unidade,
                TipoContribuicao.entrega_outra_unidade,
            )
            and self.cod_unidade_autorizadora_entrega is not None
        ):
            raise ValueError(
                "cod_unidade_autorizadora_entrega só pode ser utilizado se "
                "tipo_contribuicao for 1 ou 3"
            )
        return self

    @field_validator("percentual_contribuicao")
    @staticmethod
    def validate_percentual_contribuicao(percentual_contribuicao: int):
        "Valida se o percentual de contribuição está entre 0 e 100."
        if percentual_contribuicao < 0 or percentual_contribuicao > 100:
            raise ValueError("Percentual de contribuição deve estar entre 0 e 100")
        return percentual_contribuicao


class AvaliacaoRegistrosExecucaoSchema(BaseModel):
    __doc__ = AvaliacaoRegistrosExecucao.__doc__
    model_config = ConfigDict(from_attributes=True)

    id_periodo_avaliativo: str = Field(
        title="Identificador do período avaliativo",
        description=AvaliacaoRegistrosExecucao.id_periodo_avaliativo.comment,
    )
    data_inicio_periodo_avaliativo: date = Field(
        title="Data de início do período avaliativo",
        description=AvaliacaoRegistrosExecucao.data_inicio_periodo_avaliativo.comment,
    )
    data_fim_periodo_avaliativo: date = Field(
        title="Data de fim do período avaliativo",
        description=AvaliacaoRegistrosExecucao.data_fim_periodo_avaliativo.comment,
    )
    avaliacao_registros_execucao: int = Field(
        title="Avaliação dos registros de execução",
        description=AvaliacaoRegistrosExecucao.avaliacao_registros_execucao.comment,
    )
    data_avaliacao_registros_execucao: date = Field(
        title="Data da avaliação dos registros de execução",
        description=AvaliacaoRegistrosExecucao.data_avaliacao_registros_execucao.comment,
    )

    @field_validator("avaliacao_registros_execucao")
    @staticmethod
    def validate_avaliacao_registros_execucao(value: int) -> int:
        """Valida a avaliação dos registros de execução."""
        if value not in range(1, 6):
            raise ValueError(
                "Avaliação de registros de execução inválida; permitido: 1 a 5"
            )
        return value

    @model_validator(mode="after")
    def validate_data_fim_periodo_avaliativo(
        self,
    ) -> "AvaliacaoRegistrosExecucaoSchema":
        """Valida se a data de fim do período avaliativo é posterior à
        data de início do período avaliativo."""
        if self.data_fim_periodo_avaliativo < self.data_inicio_periodo_avaliativo:
            raise ValueError(
                "A data de fim do período avaliativo deve ser igual ou "
                "posterior à data de início do período avaliativo."
            )
        return self


class PlanoTrabalhoSchema(BaseModel):
    __doc__ = PlanoTrabalho.__doc__
    model_config = ConfigDict(from_attributes=True)

    origem_unidade: str = Field(
        title="Origem da unidade",
        description=PlanoTrabalho.origem_unidade.comment,
    )
    cod_unidade_autorizadora: int = Field(
        title="Código da unidade autorizadora",
        description=PlanoTrabalho.cod_unidade_autorizadora.comment,
    )
    id_plano_trabalho: str = Field(
        title="Identificador único do plano de trabalho",
        description=PlanoTrabalho.id_plano_trabalho.comment,
    )
    status: int = Field(
        title="Status do plano de trabalho",
        description=PlanoTrabalho.status.comment,
    )
    cod_unidade_executora: int = Field(
        title="Código da unidade executora",
        description=PlanoTrabalho.cod_unidade_executora.comment,
    )
    cpf_participante: str = Field(
        title="CPF do participante",
        description=PlanoTrabalho.cpf_participante.comment,
    )
    matricula_siape: str = Field(
        title="Matrícula SIAPE do participante",
        description=PlanoTrabalho.matricula_siape.comment,
    )
    data_inicio: date = Field(
        title="Data de início do plano de trabalho",
        description=PlanoTrabalho.data_inicio.comment,
    )
    data_termino: date = Field(
        title="Data de término do plano de trabalho",
        description=PlanoTrabalho.data_termino.comment,
    )
    carga_horaria_disponivel: int = Field(
        title="Carga horária disponível do participante",
        description=PlanoTrabalho.carga_horaria_disponivel.comment,
    )

    contribuicoes: Optional[List[ContribuicaoSchema]] = Field(
        default=[],
        title="Contribuições",
        description="Lista de Contribuições planejadas para o Plano de Trabalho.",
    )
    avaliacoes_registros_execucao: Optional[List[AvaliacaoRegistrosExecucaoSchema]] = (
        Field(
            default=[],
            title="Avaliações de registros de execução",
            description="Lista de avaliações de registros de execução do Plano de Trabalho.",
        )
    )
    participante: Optional["ParticipanteSchema"] = Field(
        default=None,
        title="Participante",
        description="Informações do participante do Plano de Trabalho.",
    )

    @field_validator("cpf_participante")
    @staticmethod
    def cpf_part_validate(cpf_participante: str) -> str:
        """Valida o CPF do participante."""
        return cpf_validate(cpf_participante)

    @model_validator(mode="after")
    def year_interval(self) -> "PlanoTrabalhoSchema":
        """Garante que o plano não abrange um período maior que 1 ano."""
        if over_a_year(self.data_termino, self.data_inicio) == 1:
            raise ValueError(
                "Plano de trabalho não pode abranger período maior que 1 ano"
            )
        return self

    @model_validator(mode="after")
    def must_be_sequential_dates(self) -> "PlanoTrabalhoSchema":
        "Verifica se a data de início e a data de término estão na ordem esperada."
        if self.data_inicio > self.data_termino:
            raise ValueError(
                "data_termino do Plano de Trabalho deve ser maior "
                "ou igual que data_inicio"
            )
        return self

    @model_validator(mode="after")
    def validate_data_inicio_periodo_avaliativo(
        self
    ) -> "PlanoTrabalhoSchema":
        """Valida se a data de início do período avaliativo de cada item
        das avaliacoes_registros_execucao é posterior à data de início do
        Plano de Trabalho."""
        if self.avaliacoes_registros_execucao and \
            any(
                avaliacao_registros_execucao.data_inicio_periodo_avaliativo < self.data_inicio
                for avaliacao_registros_execucao in self.avaliacoes_registros_execucao
        ):
            raise ValueError(
                "A data de início do período avaliativo deve ser posterior à "
                "data de início do Plano de Trabalho."
            )
        return self

class EntregaSchema(BaseModel):
    __doc__ = Entrega.__doc__
    model_config = ConfigDict(from_attributes=True)
    id_entrega: str = Field(
        title="Identificador único da entrega",
        description=Entrega.id_entrega.comment,
    )
    entrega_cancelada: Optional[bool] = Field(
        default=False,
        title="Entrega cancelada",
        description=Entrega.entrega_cancelada.comment,
    )
    nome_entrega: str = Field(
        title="Título da entrega",
        description=Entrega.nome_entrega.comment,
        max_length=STR_FIELD_MAX_SIZE,
    )
    meta_entrega: int = Field(
        title="Meta estipulada na inclusão no plano",
        description=Entrega.meta_entrega.comment,
    )
    tipo_meta: TipoMeta = Field(
        title="Tipo da meta",
        description=Entrega.tipo_meta.comment,
    )
    data_entrega: date = Field(
        title="Data da entrega",
        description=Entrega.data_entrega.comment,
    )
    nome_unidade_demandante: str = Field(
        title="Nome da unidade demandante",
        description=Entrega.nome_unidade_demandante.comment,
        max_length=STR_FIELD_MAX_SIZE,
    )
    nome_unidade_destinataria: str = Field(
        title="Nome da unidade destinatária",
        description=Entrega.nome_unidade_destinataria.comment,
        max_length=STR_FIELD_MAX_SIZE,
    )

    @field_validator("meta_entrega")
    @staticmethod
    def must_be_positive(meta_entrega: int) -> int:
        if meta_entrega < 0:
            raise ValueError("Valor meta_entrega deve ser positivo.")
        return meta_entrega

    @model_validator(mode="after")
    def validate_meta_percentual(self) -> "EntregaSchema":
        if (
            self.meta_entrega is not None
            and isinstance(self.meta_entrega, int)
            and self.tipo_meta == TipoMeta.percentual.value
            and not 0 <= self.meta_entrega <= 100
        ):
            raise ValueError(
                "Valor meta_entrega deve estar entre 0 e 100 "
                "quando tipo_entrega for percentual."
            )
        return self


class PlanoEntregasSchema(BaseModel):
    __doc__ = PlanoEntregas.__doc__
    model_config = ConfigDict(from_attributes=True)
    origem_unidade: str = Field(
        title="Código do sistema da unidade",
        description=PlanoEntregas.origem_unidade.comment,
    )
    cod_unidade_autorizadora: int = Field(
        title="Código da unidade autorizadora",
        description=PlanoEntregas.cod_unidade_autorizadora.comment,
    )
    cod_unidade_instituidora: int = Field(
        title="Código da unidade instituidora",
        description=PlanoEntregas.cod_unidade_instituidora.comment,
    )
    cod_unidade_executora: int = Field(
        title="Código da unidade executora",
        description=PlanoEntregas.cod_unidade_executora.comment,
    )
    id_plano_entregas: str = Field(
        title="Identificador único do plano de entregas",
        description=PlanoEntregas.id_plano_entregas.comment,
    )
    status: int = Field(
        title="Status do plano de entregas",
        description=PlanoEntregas.status.comment,
    )
    data_inicio: date = Field(
        title="Data de início do plano de entregas",
        description=PlanoEntregas.data_inicio.comment,
    )
    data_termino: date = Field(
        title="Data de término do plano de entregas",
        description=PlanoEntregas.data_termino.comment,
    )
    avaliacao: Optional[int] = Field(
        title="Avaliação do plano de entregas",
        description=PlanoEntregas.avaliacao.comment,
    )
    data_avaliacao: Optional[date] = Field(
        title="Data de avaliação do plano de entregas",
        description=PlanoEntregas.data_avaliacao.comment,
    )
    entregas: List[EntregaSchema] = Field(
        default=[],
        title="Entregas",
        description="Lista de entregas associadas ao Plano de Entregas",
    )

    @field_validator(
        "cod_unidade_autorizadora", "cod_unidade_instituidora", "cod_unidade_executora"
    )
    @staticmethod
    def validate_codigo_unidade(value: int) -> int:
        """Valida o código da unidade."""
        if value < 1:
            raise ValueError(f"Código da unidade inválido: {value}")
        return value

    @model_validator(mode="after")
    def validate_data_termino(self) -> "PlanoEntregasSchema":
        """Valida a data de término do plano de entregas."""
        if self.data_termino < self.data_inicio:
            raise ValueError("data_termino deve ser maior ou igual que data_inicio.")
        return self

    @model_validator(mode="after")
    def validate_data_avaliacao(self) -> "PlanoEntregasSchema":
        """Valida a data de avaliação do plano de entregas."""
        if self.data_avaliacao is not None and self.data_avaliacao < self.data_inicio:
            raise ValueError(
                "Data de avaliação deve ser maior ou igual à data de início"
            )
        return self

    @model_validator(mode="after")
    def validate_entregas_uniqueness(self) -> "PlanoEntregasSchema":
        """Valida a unicidade das entregas."""
        entregas_ids = [entrega.id_entrega for entrega in self.entregas]
        if len(entregas_ids) != len(set(entregas_ids)):
            raise ValueError("Entregas devem possuir id_entrega diferentes")
        return self

    @model_validator(mode="after")
    def validate_period(self) -> "PlanoEntregasSchema":
        """Valida o período do plano de entregas."""
        if over_a_year(self.data_termino, self.data_inicio) > 1:
            raise ValueError(
                "Plano de entregas não pode abranger período maior que 1 ano"
            )
        if self.data_termino < self.data_inicio:
            raise ValueError("Data de término deve ser maior ou igual à data de início")
        if self.data_avaliacao is not None and self.data_avaliacao < self.data_inicio:
            raise ValueError(
                "Data de avaliação deve ser maior ou igual à data de início"
            )
        return self

    @model_validator(mode="after")
    def validate_status(self) -> "PlanoEntregasSchema":
        """Verifica se o status possui valor válido."""
        if self.status not in range(1, 6):
            raise ValueError("Status inválido; permitido: 1, 2, 3, 4, 5")
        if self.status == 5 and (self.avaliacao is None or self.data_avaliacao is None):
            raise ValueError(
                "O status 5 só poderá ser usado se os campos avaliacao e "
                "data_avaliacao estiverem preenchidos."
            )
        return self

    @field_validator("avaliacao")
    @staticmethod
    def validate_avaliacao(value: int) -> int:
        """Verifica se a avaliação possui um valor válido."""
        if value is not None and value not in range(1, 6):
            raise ValueError("Nota de avaliação inválida; permitido: 1, 2, 3, 4, 5")
        return value


class ParticipanteSchema(BaseModel):
    __doc__ = Participante.__doc__
    model_config = ConfigDict(from_attributes=True)
    origem_unidade: str = Field(
        title="Código do sistema da unidade (SIAPE ou SIORG)",
        description=Participante.origem_unidade.comment,
    )
    cod_unidade_autorizadora: int = Field(
        title="Código da unidade organizacional autorizadora do PGD",
        description=Participante.cod_unidade_autorizadora.comment,
    )
    cod_unidade_lotacao: int = Field(
        title="Código da unidade organizacional de lotação do participante",
        description=Participante.cod_unidade_lotacao.comment,
    )
    matricula_siape: str = Field(
        title="Número da matrícula do participante no SIAPE",
        description=Participante.matricula_siape.comment,
    )
    cod_unidade_instituidora: int = Field(
        title="Código da unidade organizacional instituidora do PGD",
        description=Participante.cod_unidade_instituidora.comment,
    )
    cpf: str = Field(
        title="Número do CPF do agente público", description=Participante.cpf.comment
    )
    situacao: int = Field(
        title="Situação do agente público no PGD",
        description=Participante.situacao.comment,
    )
    modalidade_execucao: int = Field(
        title="Modalidade e regime de execução do trabalho",
        description=Participante.modalidade_execucao.comment,
    )
    data_assinatura_tcr: Optional[datetime] = Field(
        title="Data de assinatura do TCR",
        description=Participante.data_assinatura_tcr.comment,
    )

    @field_validator("situacao")
    @staticmethod
    def validate_situacao(value):
        "Verifica se o campo 'situacao' tem um dos valores permitidos"
        if value not in [0, 1]:
            raise ValueError("Valor do campo 'situacao' inválido; permitido: 0, 1")
        return value

    @field_validator("modalidade_execucao")
    @staticmethod
    def validate_modalidade_execucao(value):
        "Verifica se o campo 'modalidade_execucao' tem um dos valores permitidos"
        if value not in set(ModalidadesExecucao):
            raise ValueError(
                "Modalidade de execução inválida; permitido: "
                + ", ".join(
                    [str(modalidade.value) for modalidade in ModalidadesExecucao]
                )
            )
        return value

    @field_validator("matricula_siape")
    @staticmethod
    def matricula_siape_validate(matricula_siape: str) -> str:
        "Valida a matrícula SIAPE do participante."
        if len(matricula_siape) != 7:
            raise ValueError("Matrícula SIAPE deve ter 7 dígitos.")
        if not matricula_siape.isdecimal():
            raise ValueError("Matricula SIAPE deve ser numérica.")
        if len(set(matricula_siape)) < 2:
            raise ValueError("Matricula SIAPE inválida.")
        return matricula_siape

    @field_validator("cpf")
    @staticmethod
    def cpf_part_validate(cpf: str) -> str:
        "Valida o CPF do participante."
        return cpf_validate(cpf)

    @field_validator("data_assinatura_tcr")
    @staticmethod
    def data_assinatura_tcr_validate(data_assinatura_tcr: datetime) -> datetime:
        "Valida a data de assinatura do TCR."
        if data_assinatura_tcr > datetime.now():
            raise ValueError("A data_assinatura_tcr não pode ser data futura.")
        return data_assinatura_tcr


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UsersInputSchema(BaseModel):
    __doc__ = Users.__doc__
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr = Field(
        title="e-mail do usuário",
        description=Users.email.comment,
    )


class UsersGetSchema(UsersInputSchema):
    """Esquema usado para responder a consultas à API sobre usuários, por
    meio do método HTTP GET.

    Campos ocultos não são mostrados.
    """

    model_config = ConfigDict(from_attributes=True)
    is_admin: bool = Field(
        title="se o usuário será administrador da api-pgd",
        default=False,
        description=Users.is_admin.comment,
    )
    disabled: bool = Field(
        title="se o usuário está ativo",
        default=False,
        description=Users.disabled.comment,
    )
    origem_unidade: str = Field(
        title="Código do sistema da unidade (SIAPE ou SIORG)",
        description=Users.origem_unidade.comment,
    )
    cod_unidade_autorizadora: int = Field(
        title="Código da organização que autorizou o PGD",
        description=Users.cod_unidade_autorizadora.comment,
    )


class UsersSchema(UsersGetSchema):
    password: str = Field(
        title="password encriptado",
        description=Users.password.comment,
    )

    @field_validator("cod_unidade_autorizadora")
    @staticmethod
    def must_be_positive(cod_unidade: int) -> int:
        if cod_unidade < 1:
            raise ValueError("cod_SIAPE inválido")
        return cod_unidade
