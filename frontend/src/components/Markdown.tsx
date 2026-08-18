/**
 * A deliberately small Markdown renderer.
 *
 * Guide text is written by the owner in the admin section, so it is rendered as
 * React elements rather than injected HTML: there is no `dangerouslySetInnerHTML`
 * anywhere in this project, which removes the whole class of stored-XSS bugs a
 * CMS normally invites. Supported: paragraphs, bullet lists, bold, italic,
 * inline code and links.
 */

import { Fragment, type ReactNode } from 'react';

const INLINE = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)\s]+\))/g;
const SAFE_LINK = /^(https?:|mailto:|tel:|\/)/i;

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  return text.split(INLINE).map((token, index) => {
    const key = `${keyPrefix}-${index}`;
    if (token.startsWith('**') && token.endsWith('**')) {
      return <strong key={key}>{token.slice(2, -2)}</strong>;
    }
    if (token.startsWith('*') && token.endsWith('*') && token.length > 2) {
      return <em key={key}>{token.slice(1, -1)}</em>;
    }
    if (token.startsWith('`') && token.endsWith('`')) {
      return <code key={key}>{token.slice(1, -1)}</code>;
    }
    const link = /^\[([^\]]+)\]\(([^)\s]+)\)$/.exec(token);
    if (link?.[1] && link[2]) {
      const [, label, href] = link;
      // Anything that is not an ordinary link is shown as plain text rather
      // than trusted, so a pasted `javascript:` URL cannot become a handler.
      if (!SAFE_LINK.test(href)) return <Fragment key={key}>{label}</Fragment>;
      const external = /^https?:/i.test(href);
      return (
        <a
          key={key}
          href={href}
          {...(external ? { target: '_blank', rel: 'noreferrer noopener' } : {})}
        >
          {label}
        </a>
      );
    }
    return <Fragment key={key}>{token}</Fragment>;
  });
}

export function Markdown({ text, className }: { text: string; className?: string }) {
  const blocks = text.trim().split(/\n{2,}/);

  return (
    <div className={className ?? 'prose-house'}>
      {blocks.map((block, blockIndex) => {
        const lines = block.split('\n');
        const isList = lines.every((line) => line.trimStart().startsWith('- '));

        if (isList) {
          return (
            <ul key={blockIndex} className="list-disc space-y-1.5 pl-5">
              {lines.map((line, lineIndex) => (
                <li key={lineIndex}>
                  {renderInline(line.trimStart().slice(2), `${blockIndex}-${lineIndex}`)}
                </li>
              ))}
            </ul>
          );
        }

        return (
          <p key={blockIndex} className={blockIndex > 0 ? 'mt-3' : undefined}>
            {renderInline(block.replaceAll('\n', ' '), String(blockIndex))}
          </p>
        );
      })}
    </div>
  );
}
