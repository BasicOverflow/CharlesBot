import Navitem from "./navitem"


const Navbar = () => {
    return (
        <div className="navbar" style={{ 'align':'center' }}>
            <Navitem page="#" title="About"/>
            <Navitem page="#" title="How to Use"/>
            <Navitem page="#" title="Download Client"/>
        </div>
    )
}

export default Navbar
