from pydantic import BaseModel


class Artifact(BaseModel):

    artifact_type: str

    name: str

    table: str | None = None

    when: str | None = None

    insert: bool | None = None

    update: bool | None = None

    type: str | None = None

    script: str