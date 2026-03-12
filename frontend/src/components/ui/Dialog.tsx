// Dialog – modal dialog component.
"use client";

import { useEffect, useRef } from "react";

interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export default function Dialog({ open, onClose, title, children }: DialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const el = dialogRef.current;
    if (!el) return;
    if (open && !el.open) el.showModal();
    else if (!open && el.open) el.close();
  }, [open]);

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      className="glass-panel p-8 max-w-lg w-full backdrop:bg-black/30 rounded-2xl"
    >
      <h2 className="text-xl font-bold text-brand-dark mb-4">{title}</h2>
      {children}
      <div className="mt-6 flex justify-end">
        <button
          onClick={onClose}
          className="btn-gradient text-white px-8 py-2.5 rounded-[0.625rem] font-semibold"
        >
          Confirm
        </button>
      </div>
    </dialog>
  );
}
