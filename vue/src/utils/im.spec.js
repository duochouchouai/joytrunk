import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { truncateText, validateImageUrl, isMuted } from './im';

describe('im utils', () => {
  describe('truncateText', () => {
    it('returns empty string for null/undefined', () => {
      expect(truncateText(null)).toBe('');
      expect(truncateText(undefined)).toBe('');
    });

    it('returns empty string for empty string', () => {
      expect(truncateText('')).toBe('');
    });

    it('trims and returns as-is when length <= maxLen', () => {
      expect(truncateText('  short  ', 20)).toBe('short');
      expect(truncateText('exactly20charswow!!!', 20)).toBe('exactly20charswow!!!');
    });

    it('appends ... only when length > maxLen', () => {
      expect(truncateText('this is 21 characters!!', 20)).toBe('this is 21 character...');
      expect(truncateText('ab', 1)).toBe('a...');
    });

    it('uses default maxLen 20', () => {
      const long = '12345678901234567890x';
      expect(truncateText(long)).toBe('12345678901234567890...');
    });
  });

  describe('validateImageUrl', () => {
    it('returns false for null/undefined/empty', () => {
      expect(validateImageUrl(null)).toBe(false);
      expect(validateImageUrl(undefined)).toBe(false);
      expect(validateImageUrl('')).toBe(false);
    });

    it('returns true for http and https', () => {
      expect(validateImageUrl('http://example.com/img.png')).toBe(true);
      expect(validateImageUrl('https://example.com/img.png')).toBe(true);
      expect(validateImageUrl('  https://x.co  ')).toBe(true);
    });

    it('returns false for non-URL', () => {
      expect(validateImageUrl('ftp://x.com')).toBe(false);
      expect(validateImageUrl('not a url')).toBe(false);
    });
  });

  describe('isMuted', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });
    afterEach(() => {
      vi.useRealTimers();
    });

    it('returns false for null/undefined/empty', () => {
      expect(isMuted(null)).toBe(false);
      expect(isMuted(undefined)).toBe(false);
    });

    it('returns false when muted_until is in the past', () => {
      const past = new Date(Date.now() - 60000).toISOString();
      expect(isMuted(past)).toBe(false);
    });

    it('returns true when muted_until is in the future', () => {
      const future = new Date(Date.now() + 60000).toISOString();
      expect(isMuted(future)).toBe(true);
    });
  });
});
