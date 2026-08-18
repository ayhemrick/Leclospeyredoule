import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Markdown } from './Markdown';

describe('Markdown', () => {
  it('renders paragraphs separately', () => {
    render(<Markdown text={'First paragraph.\n\nSecond paragraph.'} />);
    expect(screen.getByText('First paragraph.')).toBeInTheDocument();
    expect(screen.getByText('Second paragraph.')).toBeInTheDocument();
  });

  it('renders bold, italic and inline code', () => {
    render(<Markdown text={'A **bold** and *soft* word with `code`.'} />);
    expect(screen.getByText('bold').tagName).toBe('STRONG');
    expect(screen.getByText('soft').tagName).toBe('EM');
    expect(screen.getByText('code').tagName).toBe('CODE');
  });

  it('renders bullet lists', () => {
    render(<Markdown text={'- first\n- second\n- third'} />);
    expect(screen.getAllByRole('listitem')).toHaveLength(3);
  });

  it('opens external links safely in a new tab', () => {
    render(<Markdown text="See [the citadel](https://example.com/citadel)." />);
    const link = screen.getByRole('link', { name: 'the citadel' });
    expect(link).toHaveAttribute('href', 'https://example.com/citadel');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', expect.stringContaining('noopener'));
  });

  it('keeps internal links in the same tab', () => {
    render(<Markdown text="Back to [the guide](/guide)." />);
    const link = screen.getByRole('link', { name: 'the guide' });
    expect(link).not.toHaveAttribute('target');
  });

  it('refuses to make a javascript: URL clickable', () => {
    render(<Markdown text="[click me](javascript:danger)" />);
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    expect(screen.getByText('click me')).toBeInTheDocument();
  });

  it('refuses a data: URL too', () => {
    render(<Markdown text="[open](data:text/html;base64,PHNjcmlwdD4=)" />);
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });

  it('never injects raw HTML from the content', () => {
    const { container } = render(<Markdown text={'<img src=x onerror="alert(1)">'} />);
    expect(container.querySelector('img')).toBeNull();
    expect(container.textContent).toContain('<img src=x onerror="alert(1)">');
  });
});
