import { forwardRef } from 'preact/compat'
import Progress from '../Progress/Progress'
import './ReaderContent.css'

export const ReaderContent = forwardRef(function ReaderContent({ article, progress, settings }, ref) {
  const { font, size, spacing } = settings

  return (
    <div className="reader-content" ref={ref}>
      <Progress value={progress} className="reader-progress-bar" />

      {/* Article content */}
      <article className={`reader-article ${font} size-${size} ${spacing}`}>
        <h1>{article?.title}</h1>
        <div dangerouslySetInnerHTML={{ __html: article?.content || '' }} />
      </article>

      {/* Bottom bar with title and percentage */}
      <div className="reader-bottom-bar">
        <span className="reader-bottom-title">{article?.title}</span>
        <span className="reader-bottom-progress">{Math.round(progress)}%</span>
      </div>
    </div>
  )
})
