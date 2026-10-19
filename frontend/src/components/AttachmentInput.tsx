import { useEffect, useRef, useState } from "react";
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

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function AttachmentInput({ file, onChange }: AttachmentInputProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

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

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) handleFileSelect(dropped);
  }

  if (file) {
    return (
      <FormField label="Attachment" hint="Image, PDF, or log file — up to 10MB">
        <div className="attachment-preview">
          {previewUrl ? (
            <img src={previewUrl} alt="Attachment preview" className="attachment-preview-thumb" />
          ) : (
            <div className="attachment-preview-icon">{ACCEPTED_TYPES[file.type] ?? "File"}</div>
          )}
          <div className="attachment-preview-meta">
            <span className="attachment-preview-name">{file.name}</span>
            <span className="attachment-preview-size">{formatFileSize(file.size)}</span>
          </div>
          <button
            type="button"
            className="link-button attachment-preview-remove"
            onClick={() => {
              handleFileSelect(null);
              if (inputRef.current) inputRef.current.value = "";
            }}
          >
            Remove
          </button>
        </div>
      </FormField>
    );
  }

  return (
    <FormField label="Attachment" htmlFor="attachment" hint="Image, PDF, or log file — optional, up to 10MB">
      <div
        className={`attachment-dropzone${dragOver ? " attachment-dropzone-active" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") inputRef.current?.click(); }}
        aria-label="Upload attachment — click or drag and drop"
      >
        <span className="attachment-dropzone-icon">📎</span>
        <span className="attachment-dropzone-text">
          {dragOver ? "Drop to attach" : "Click or drag to attach a file"}
        </span>
        <span className="attachment-dropzone-hint">PNG, JPEG, PDF, or plain text · max 10MB</span>
      </div>
      <input
        ref={inputRef}
        id="attachment"
        type="file"
        accept={Object.keys(ACCEPTED_TYPES).join(",")}
        onChange={(e) => handleFileSelect(e.target.files?.[0] ?? null)}
        style={{ display: "none" }}
      />
    </FormField>
  );
}
