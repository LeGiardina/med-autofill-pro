from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from db import Base
class Template(Base):
    __tablename__='templates'
    id:Mapped[int]=mapped_column(Integer, primary_key=True)
    slug:Mapped[str]=mapped_column(String(128), unique=True, index=True)
    title:Mapped[str]=mapped_column(String(256))
    diagnosis_icd10:Mapped[str|None]=mapped_column(String(32), nullable=True)
    diagnosis_snomed:Mapped[str|None]=mapped_column(String(64), nullable=True)
    tags:Mapped[str|None]=mapped_column(String(256), nullable=True)
    body_md:Mapped[str]=mapped_column(Text)
    variables:Mapped[str|None]=mapped_column(Text, nullable=True)
    links:Mapped[str|None]=mapped_column(Text, nullable=True)
    status:Mapped[str]=mapped_column(String(32), default='draft')
    version:Mapped[int]=mapped_column(Integer, default=1)
    updated_by:Mapped[str|None]=mapped_column(String(128), nullable=True)
    change_note:Mapped[str|None]=mapped_column(Text, nullable=True)
    def to_dict(self):
        import json
        return {'id':self.id,'slug':self.slug,'title':self.title,'diagnosis_icd10':self.diagnosis_icd10,
                'diagnosis_snomed':self.diagnosis_snomed,'tags':self.tags.split(',') if self.tags else [],
                'body_md':self.body_md,'variables':json.loads(self.variables) if self.variables else [],
                'links':json.loads(self.links) if self.links else [], 'status':self.status,'version':self.version,
                'updated_by':self.updated_by,'change_note':self.change_note}
