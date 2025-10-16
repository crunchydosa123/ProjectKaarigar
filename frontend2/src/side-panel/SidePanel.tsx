import { usePage } from '@/contexts/PageContext';
import React from 'react'

type Props = {}

const SidePanel = (props: Props) => {
  const { currentPage } = usePage();
  return (
    <div>{currentPage}</div>
  )
}

export default SidePanel