import InsideProduct from '@/components/InsideProduct';

export default function LeopardPage() {
    return (
        <InsideProduct
            productName="Leopard"
            primaryColor="#5C3A1E"
            accentColor="#B87333"
            techs={['LeapCore', 'ShockSphere', 'NanoSpread']}
            seal={null}
            archProfiles={['Low', 'Medium', 'High']}
        />
    );
}
