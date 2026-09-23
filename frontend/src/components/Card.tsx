import type { ReactNode } from 'react'
import './Card.css'

interface CardProps {
  title?: string
  description?: string
  children: ReactNode
}

function Card({ title, description, children }: CardProps) {
  return (
    <section className="card">
      {title ? <h2 className="card-title">{title}</h2> : null}
      {description ? <p className="card-description">{description}</p> : null}
      <div>{children}</div>
    </section>
  )
}

export default Card
