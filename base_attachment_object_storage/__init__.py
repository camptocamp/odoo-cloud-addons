from . import models
from odoo.http import Stream


old_from_attachment = Stream.as_attachment


@classmethod
def from_attachment(cls, attachment):
    if attachment.store_fname and attachment._is_file_from_a_store(
        attachment.store_fname
    ):
        self = cls(
            mimetype=attachment.mimetype,
            download_name=attachment.name,
            conditional=True,
            etag=attachment.checksum,
        )
        self.type = "data"
        self.data = attachment.raw
        self.size = len(self.data)
        return self
    return old_from_attachment(attachment)


Stream.as_attachment = from_attachment
