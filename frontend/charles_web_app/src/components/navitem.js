

const Navitem = ({ title, page }) => {
    return (
        <a style={ {'color':'navy', 'padding':'5px'} } href= { page } > { title } </a>
    )
}

export default Navitem
