import { describe, it, expect } from 'vitest';
import { getReadableSource } from './sourceFormatter.js';

describe('getReadableSource', () => {
  describe('Formatted file strings from DB', () => {
    it('should handle "Epub File: added [date]" format', () => {
      expect(getReadableSource('Epub File: added September 12, 2022')).toBe('EPUB');
      expect(getReadableSource('Epub File: added December 23, 2023')).toBe('EPUB');
    });

    it('should handle "PDF File: added [date]" format', () => {
      expect(getReadableSource('PDF File: added September 02, 2024')).toBe('PDF');
      expect(getReadableSource('PDF File: added December 06, 2021')).toBe('PDF');
    });

    it('should handle "manually added [date]" format', () => {
      expect(getReadableSource('manually added February 11, 2022')).toBe('Manual');
      expect(getReadableSource('manually added November 24, 2020')).toBe('Manual');
    });
  });

  describe('EPUB and PDF files', () => {
    it('should return EPUB for .epub extension', () => {
      expect(getReadableSource('article.epub')).toBe('EPUB');
      expect(getReadableSource('/path/to/book.epub')).toBe('EPUB');
      expect(getReadableSource('BOOK.EPUB')).toBe('EPUB');
    });

    it('should return PDF for .pdf extension', () => {
      expect(getReadableSource('document.pdf')).toBe('PDF');
      expect(getReadableSource('/path/to/document.pdf')).toBe('PDF');
    });
  });

  describe('Clean names from DB', () => {
    it('should preserve short clean names', () => {
      expect(getReadableSource('Washington Post')).toBe('Washington Post');
      expect(getReadableSource('Farnam Street')).toBe('Farnam Street');
      expect(getReadableSource('LinkedIn post')).toBe('LinkedIn post');
      expect(getReadableSource('German class')).toBe('German class');
      expect(getReadableSource('Codeworks')).toBe('Codeworks');
      expect(getReadableSource('Book')).toBe('Book');
      expect(getReadableSource('NYT')).toBe('NYT');
    });

    it('should truncate long clean names with ellipsis', () => {
      expect(getReadableSource('This is a very long clean name that exceeds twenty characters')).toBe('This is a very long ...');
    });
  });

  describe('Real URLs from DB', () => {
    it('should handle New York Times URLs', () => {
      expect(getReadableSource('https://www.nytimes.com/2024/10/07/opinion/novelist-back-to-school-behavioral-science-identity.html?unlocked_article_code=1.QU4.FJTD.Is5XRghY9vMt&mc_cid=13ca65e521&mc_eid=64d208ece4')).toBe('Nytimes');
    });

    it('should handle Fortune URLs', () => {
      expect(getReadableSource('https://fortune.com/longform/wnba-cathy-engelbert-nba-caitlin-clark-angel-reese-nike-basketball/?nba224=&utm_source=substack&utm_medium=email')).toBe('Fortune');
    });

    it('should handle New Yorker URLs', () => {
      expect(getReadableSource('https://www.newyorker.com/culture/open-questions/does-anyone-really-know-you?mc_cid=13ca65e521&mc_eid=64d208ece4')).toBe('Newyorker');
    });

    it('should handle Reddit URLs', () => {
      expect(getReadableSource('https://www.reddit.com/r/ableton/comments/5rjqer/apc40_vs_apc40_mkii/')).toBe('Reddit');
    });

    it('should handle Medium URLs', () => {
      expect(getReadableSource('https://byrnehobart.medium.com/writing-is-networking-for-introverts-5cac14ad4c77')).toBe('Byrnehobart');
    });

    it('should handle Patreon URLs', () => {
      expect(getReadableSource('https://www.patreon.com/posts/ratcheting-in-47976114')).toBe('Patreon');
    });

    it('should handle YouTube URLs', () => {
      expect(getReadableSource('https://www.youtube.com/watch?v=KJ3rf5QbUkg')).toBe('Youtube');
    });

    it('should handle Hacker News URLs', () => {
      expect(getReadableSource('https://news.ycombinator.com/item?id=25217436')).toBe('News');
    });

    it('should handle archive URLs', () => {
      expect(getReadableSource('https://archive.is/obKte')).toBe('Archive');
      expect(getReadableSource('https://archive.ph/v1vzU')).toBe('Archive');
    });

    it('should handle threadreader URLs', () => {
      expect(getReadableSource('https://threadreaderapp.com/thread/1379844845536223235.html')).toBe('Threadreaderapp');
    });

    it('should handle international domains', () => {
      expect(getReadableSource('https://www.nexojornal.com.br/colunistas/2025/03/05/so-da-para-entender-trump-a-partir-do-conflito-com-a-china?utm_medium=email')).toBe('Nexojornal');
      expect(getReadableSource('https://www.masterstudies.com/Masters-Degree-Programme-in-Peace-Mediation-and-Conflict-Research/Finland/%C3%85bo-Akademi-University/')).toBe('Masterstudies');
    });
  });

  describe('Subdomains', () => {
    it('should extract subdomain from blog URLs', () => {
      expect(getReadableSource('blog.medium.com/article')).toBe('Blog');
    });

    it('should extract subdomain from news URLs', () => {
      expect(getReadableSource('news.ycombinator.com/item')).toBe('News');
    });
  });

  describe('Edge cases', () => {
    it('should return Unknown for empty or null', () => {
      expect(getReadableSource('')).toBe('Unknown');
      expect(getReadableSource(null)).toBe('Unknown');
      expect(getReadableSource(undefined)).toBe('Unknown');
    });

    it('should handle malformed inputs gracefully', () => {
      // Single dot gets parsed by URL but has empty hostname, so returns original
      expect(getReadableSource('.')).toBe('.');
      // Protocol-only URL returns original since hostname is empty
      expect(getReadableSource('https://')).toBe('https://');
    });

    it('should truncate fallback values over 20 chars', () => {
      const longString = 'this is a very long string that should be truncated';
      const result = getReadableSource(longString);
      expect(result).toBe('this is a very long ...');
      expect(result.length).toBeLessThanOrEqual(23); // 20 + '...'
    });
  });

  describe('Real edge cases from DB', () => {
    it('should handle single letter or short entries', () => {
      expect(getReadableSource('Hi')).toBe('Hi');
      expect(getReadableSource('sdf')).toBe('sdf');
    });

    it('should handle blog names', () => {
      expect(getReadableSource('FS Blog')).toBe('FS Blog');
      // Truncates at exactly 20 chars before adding ellipsis
      expect(getReadableSource('Center for Progressive Reform blog')).toBe('Center for Progressi...');
    });
  });
});
