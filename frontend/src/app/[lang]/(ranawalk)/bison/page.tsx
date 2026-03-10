import InsideProduct from '@/components/InsideProduct';

export default function BisonPage() {
    return (
        <InsideProduct
            productName="Bison"
            primaryColor="#2C2C2C"
            accentColor="#FF8C00"
            techs={['LeapCore', 'PORON_XRD', 'NanoSpread']}
            seal="American Technology Inside"
            archProfiles={['Low', 'Medium', 'High']}
        />
    );
}
