import { useEffect, useState } from "react";
import FormField from "./FormField";

const ACCEPTED_TYPES: Record<string, string> = {
  "image/png": "Image",
  "image/jpeg": "Image",
  "application/pdf": "PDF",
  "text/plain": "Log/text",
  "text/x-log": "Log/text",
};
const MAX_SIZE_MB = 10;

interface AttachmentInputProps {
  file: File | null;
  onChange: (file: File | null, error: string | null) => void;
}

// Client-side type/size validation mirrors the backend's own checks
// (app/routers/tickets.py's _ATTACHMENT_TYPES and settings.max_upload_size_mb) so a
// bad file is rejected before upload instead of round-tripping to the server first.
function validate(file: File): string | null {
  if (!(file.type in ACCEPTED_TYPES)) {
    return "Unsupported file type — attach an image (PNG/JPEG), a PDF, or a log/text file.";
  }
  if (file.size > MAX_SIZE_MB * 1024 * 1024) {
    return `File is too large — the limit is ${MAX_SIZE_MB}MB.`;
  }
  return null;
}

export default function AttachmentInput({ file, onChange }: AttachmentInputProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!file || !file.type.startsWith("image/")) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  function handleFileSelect(selected: File | null) {
    if (!selected) {
      onChange(null, null);
      return;
    }
    const error = validate(selected);
    onChange(error ? null : selected, error);
  }

  return (
    <FormField label="Attachment" htmlFor="attachment" hint="Image, PDF, or log file — optional, up to 10MB">
      <input
        id="attachment"
        type="file"
        accept={Object.keys(ACCEPTED_TYPES).join(",")}
        onChange={(e) => handleFileSelect(e.target.files?.[0] ?? null)}
      />
      {file && (
        <div className="attachment-preview">
          {previewUrl ? (
            <img src={previewUrl} alt="Attachment preview" className="attachment-preview-thumb" />
          ) : (
            <div className="attachment-preview-icon">{ACCEPTED_TYPES[file.type] ?? "File"}</div>
          )}
          <div className="attachment-preview-meta">
            <span className="attachment-preview-name">{file.name}</span>
            <span className="attachment-preview-size">{(file.size / 1024).toFixed(0)} KB</span>
          </div>
          <button
            type="button"
            className="link-button attachment-preview-remove"
            onClick={() => handleFileSelect(null)}
          >
            Remove
          </button>
        </div>
      )}
    </FormField>
  );
}
