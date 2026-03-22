"use client";

import { useState } from 'react';
import toast from 'react-hot-toast';

interface FormSubmitOptions<T> {
  onSuccess?: (result: T) => void;
  onError?: (err: any) => void;
  successMessage?: string;
}

export function useFormSubmit<T>(
  onSubmit: (data: any) => Promise<T>,
  options: FormSubmitOptions<T> = {}
) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: any) => {
    setSubmitting(true);
    setError(null);
    try {
      const result = await onSubmit(data);
      if (options.successMessage) {
        toast.success(options.successMessage);
      }
      options.onSuccess?.(result);
      return result;
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Error processing form';
      setError(msg);
      toast.error(msg);
      options.onError?.(err);
      throw err;
    } finally {
      setSubmitting(false);
    }
  };

  return { handleSubmit, submitting, error, setError };
}
